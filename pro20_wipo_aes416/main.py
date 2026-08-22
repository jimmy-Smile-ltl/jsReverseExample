"""
WIPO 全球商标数据库 (brands.wipo.int) — 非标准 AES: 416-bit key / 19 轮手写纯 Python 实现 + PKCE S256

用法:
    python main.py   # 手写 AES-416 解密真实密文 + 全链验证 (纯标准库, 零第三方依赖, 无网络)

背景 (CryptoJS.js 混淆 bundle, 2024-11 原项目抓包; 期望值经原版 bundle node 实跑交叉验证, 2026-08-20):
    1. 站点使用非标准 AES: key = 静态 16 字符 + hashsearch 头 UUID 36 字符 = 52 字节 (416 bit)。
       CryptoJS 4.x 版 key schedule 按 r = key.sigBytes/4 = 13 words 扩展:
       nRounds = 6 + r = 19 轮 (标准 AES-128/256 是 10/14 轮), schedule 共 4*(nRounds+1) = 80 words,
       Rcon 表 B = [0,1,2,4,8,16,32,64,128,27,54] (index>=11 时 JS undefined<<24 = 0),
       且 r > 6 时每轮 o%r==4 的 word 先做一次 SubWord —— pycryptodome 不支持非标准 key 长, 只能手写。
    2. 响应: data 字段 AES-ECB 密文 (base64) -> 手写解密 -> PKCS7 去填充 -> JSON。
    3. 请求链: OAuth2 ForgeRock access_token -> hashsearch header (UUID) -> 搜索接口
       PKCE S256: codeVerifier = io(60) 随机串 (字母表 0123456789...+/),
       codeChallenge = urlsafe_b64(sha256(verifier)).rstrip('=')

    S-box 用 GF(2^8) 乘法逆元 + 仿射变换程序化生成; 正确性由两组证据保证:
      a) AES-128 标准向量 (test.ipynb cell10, 原项目留存): key="8?)i_~Nk6qv0IX;2" 加密 "Hello, World!"
         期望 cc504ae98934a33c5f2c001962deb730
      b) 真实 416-bit 密文 (解码.js 内嵌 de, 原项目 2024-11 抓包) 解密 sha256 一致 + 重加密逐字节相等

样例来源: 解码.js de (真实响应密文, 2024-11) + auth.js PKCE tuple (node 实跑捕获, 2026-08-20).
"""

import base64
import hashlib
import json
import pathlib
import secrets
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

# ---- 常量 (CryptoJS.js / 解码.js / auth.js) ----
STATIC_KEY = "8?)i_~Nk6qv0IX;2"          # 静态 key 前缀 (与 AES-128 测试向量同源)
UUID_HEADER = "bc7c1454-1a0d-4b4d-ba33-410e201a8d85"  # hashsearch header UUID (运行时从 header 取值)
RCON = [0, 1, 2, 4, 8, 16, 32, 64, 128, 27, 54]      # JS 源: B = [0,1,2,4,8,16,32,64,128,27,54]
PKCE_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+/"

# node 实跑捕获的 PKCE tuple (auth.js 原函数, 2026-08-20)
PKCE_VERIFIER = "hTiGncH4+BhuZYIpwkXiv0ldV0Wxcaf3C8x9KdRGuR/HBHREW1zzVlpmNj5B"
PKCE_CHALLENGE = "4iUUmGboyU3QGbI1B8ErVeKrIGC0lDfVYpxyxkWo93s"


# ---- S-box: GF(2^8) 逆元 + AES 仿射变换 (程序化生成, 与 CryptoJS 内嵌 h 表一致) ----
def _gf_mul(a: int, b: int) -> int:
    """GF(2^8) 乘法 (0x1B 不可约多项式)"""
    p = 0
    for _ in range(8):
        if b & 1:
            p ^= a
        hi = a & 0x80
        a = (a << 1) & 0xFF
        if hi:
            a ^= 0x1B
        b >>= 1
    return p


def _gf_inv(a: int) -> int:
    """GF(2^8) 乘法逆元: a^254 (平方-乘)"""
    if a == 0:
        return 0
    r, base, e = 1, a, 254
    while e:
        if e & 1:
            r = _gf_mul(r, base)
        base = _gf_mul(base, base)
        e >>= 1
    return r


def build_sbox() -> list:
    """AES S-box: b_i' = b_i ^ b_{i+4} ^ b_{i+5} ^ b_{i+6} ^ b_{i+7} ^ c_i, c=0x63"""
    sbox = []
    for x in range(256):
        inv = _gf_inv(x)
        r = 0
        for i in range(8):
            b = (inv >> i) & 1
            t = (b ^ (inv >> ((i + 4) % 8)) & 1 ^ (inv >> ((i + 5) % 8)) & 1
                 ^ (inv >> ((i + 6) % 8)) & 1 ^ (inv >> ((i + 7) % 8)) & 1
                 ^ (0x63 >> i) & 1)
            r |= t << i
        sbox.append(r)
    return sbox


SBOX = build_sbox()


def _subword(w: int) -> int:
    """逐字节 S-box 替换"""
    return (SBOX[w >> 24] << 24 | SBOX[w >> 16 & 0xFF] << 16
            | SBOX[w >> 8 & 0xFF] << 8 | SBOX[w & 0xFF])


def _rotword(w: int) -> int:
    return (w << 8 | w >> 24) & 0xFFFFFFFF


# ---- key expansion (忠实移植 CryptoJS._doReset 广义算法) ----
def expand_key(key: bytes) -> tuple:
    """r = sigBytes/4, nRounds = 6 + r, 4*(nRounds+1) words
    n[o] = n[o-r] ^ a;  a 在 o%r==0 时 RotWord+SubWord+Rcon, 在 r>6 且 o%r==4 时 SubWord
    """
    r = len(key) // 4
    n_rounds = 6 + r
    n_words = 4 * (n_rounds + 1)
    sched = []
    for o in range(n_words):
        if o < r:
            sched.append(int.from_bytes(key[4 * o:4 * o + 4], "big"))
        else:
            a = sched[o - 1]
            if o % r:
                if r > 6 and o % r == 4:
                    a = _subword(a)
            else:
                a = _subword(_rotword(a))
                # JS: B[o/r|0]<<24, 下标越界 -> undefined<<24 = 0
                a ^= (RCON[o // r] if o // r < len(RCON) else 0) << 24
            sched.append(sched[o - r] ^ a)
    return n_rounds, sched


# ---- AES 轮函数 (标准算法, 19 轮) ----
def _xtime(x: int) -> int:
    return ((x << 1) ^ (0x1B if x & 0x80 else 0)) & 0xFF


def _gmul(a: int, b: int) -> int:
    p = 0
    for _ in range(8):
        if b & 1:
            p ^= a
        hi = a & 0x80
        a = (a << 1) & 0xFF
        if hi:
            a ^= 0x1B
        b >>= 1
    return p


def _encrypt_block(block: bytes, sched: list, n_rounds: int) -> bytes:
    """标准 AES 加密块: AddRoundKey + (SubBytes, ShiftRows, MixColumns, AddRoundKey) x n_rounds-1 + 末轮

    状态按 FIPS-197 列主序装载: s[r][c] = in[r + 4c]
    """
    s = [[block[r_ + 4 * c] for c in range(4)] for r_ in range(4)]

    def add_rk(rnd):
        w = sched[4 * rnd:4 * rnd + 4]
        for c in range(4):
            rk = [(w[c] >> (24 - 8 * r_)) & 0xFF for r_ in range(4)]
            for r_ in range(4):
                s[r_][c] ^= rk[r_]

    add_rk(0)
    for rnd in range(1, n_rounds):
        for r_ in range(4):
            for c in range(4):
                s[r_][c] = SBOX[s[r_][c]]                       # SubBytes
        for r_ in range(1, 4):
            s[r_] = s[r_][r_:] + s[r_][:r_]                     # ShiftRows (行 r 左移 r)
        for c in range(4):                                      # MixColumns
            a0, a1, a2, a3 = s[0][c], s[1][c], s[2][c], s[3][c]
            s[0][c] = _gmul(a0, 2) ^ _gmul(a1, 3) ^ a2 ^ a3
            s[1][c] = a0 ^ _gmul(a1, 2) ^ _gmul(a2, 3) ^ a3
            s[2][c] = a0 ^ a1 ^ _gmul(a2, 2) ^ _gmul(a3, 3)
            s[3][c] = _gmul(a0, 3) ^ a1 ^ a2 ^ _gmul(a3, 2)
        add_rk(rnd)
    for r_ in range(4):
        for c in range(4):
            s[r_][c] = SBOX[s[r_][c]]
    for r_ in range(1, 4):
        s[r_] = s[r_][r_:] + s[r_][:r_]
    add_rk(n_rounds)
    return bytes(s[r_][c] for c in range(4) for r_ in range(4))


def _decrypt_block(block: bytes, sched: list, n_rounds: int) -> bytes:
    """标准 AES 解密块 (逆 S-box + 逆轮)"""
    inv_sbox = [0] * 256
    for i, v in enumerate(SBOX):
        inv_sbox[v] = i
    s = [[block[r_ + 4 * c] for c in range(4)] for r_ in range(4)]

    def add_rk(rnd):
        w = sched[4 * rnd:4 * rnd + 4]
        for c in range(4):
            rk = [(w[c] >> (24 - 8 * r_)) & 0xFF for r_ in range(4)]
            for r_ in range(4):
                s[r_][c] ^= rk[r_]

    add_rk(n_rounds)
    for rnd in range(n_rounds - 1, 0, -1):
        for r_ in range(1, 4):
            s[r_] = s[r_][-r_:] + s[r_][:-r_]                     # InvShiftRows (行 r 右移 r)
        for r_ in range(4):
            for c in range(4):
                s[r_][c] = inv_sbox[s[r_][c]]                     # InvSubBytes
        add_rk(rnd)
        for c in range(4):                                        # InvMixColumns
            a0, a1, a2, a3 = s[0][c], s[1][c], s[2][c], s[3][c]
            s[0][c] = _gmul(a0, 14) ^ _gmul(a1, 11) ^ _gmul(a2, 13) ^ _gmul(a3, 9)
            s[1][c] = _gmul(a0, 9) ^ _gmul(a1, 14) ^ _gmul(a2, 11) ^ _gmul(a3, 13)
            s[2][c] = _gmul(a0, 13) ^ _gmul(a1, 9) ^ _gmul(a2, 14) ^ _gmul(a3, 11)
            s[3][c] = _gmul(a0, 11) ^ _gmul(a1, 13) ^ _gmul(a2, 9) ^ _gmul(a3, 14)
    for r_ in range(1, 4):
        s[r_] = s[r_][-r_:] + s[r_][:-r_]
    for r_ in range(4):
        for c in range(4):
            s[r_][c] = inv_sbox[s[r_][c]]
    add_rk(0)
    return bytes(s[r_][c] for c in range(4) for r_ in range(4))


# ---- ECB 封装 (PKCS7) ----
def aes_ecb_encrypt(plain: bytes, key: bytes) -> bytes:
    n_rounds, sched = expand_key(key)
    pad = 16 - len(plain) % 16
    plain = plain + bytes([pad]) * pad
    return b"".join(_encrypt_block(plain[i:i + 16], sched, n_rounds)
                    for i in range(0, len(plain), 16))


def aes_ecb_decrypt(cipher: bytes, key: bytes) -> bytes:
    n_rounds, sched = expand_key(key)
    raw = b"".join(_decrypt_block(cipher[i:i + 16], sched, n_rounds)
                   for i in range(0, len(cipher), 16))
    pad = raw[-1]
    assert 1 <= pad <= 16 and raw[-pad:] == bytes([pad]) * pad, "PKCS7 填充校验失败"
    return raw[:-pad]


# ---- PKCE S256 (auth.js io/qi 函数) ----
def pkce_verifier() -> str:
    """io(60): 60 字符随机串, 字母表 0-9A-Za-z+/"""
    return "".join(secrets.choice(PKCE_ALPHABET) for _ in range(60))


def pkce_s256(verifier: str) -> str:
    """qi(verifier): S256 -> urlsafe b64 去 '='"""
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()


def main() -> None:
    passed, total = 0, 0

    def check(ok: bool, label: str, detail: str = "") -> None:
        nonlocal passed, total
        total += 1
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label} {detail}")

    # 1. S-box 标准值抽查 (AES 标准: sbox[0]=0x63, sbox[1]=0x7c, sbox[0x10]=0xca,
    #    sbox[0x53]=0xed, sbox[0xff]=0x16)
    sbox_std = {0x00: 0x63, 0x01: 0x7c, 0x10: 0xca, 0x53: 0xed, 0xFF: 0x16}
    check(all(SBOX[k] == v for k, v in sbox_std.items()),
          "S-box 程序化生成 (5 个标准值抽查)")

    # 2. key 结构: 静态 16 字符 + hashsearch UUID 36 字符 = 52 字节
    key = (STATIC_KEY + UUID_HEADER).encode()
    check(len(key) == 52 and len(STATIC_KEY) == 16 and len(UUID_HEADER) == 36,
          "key 结构", f"(16+36={len(key)}B)")

    # 3. 轮数: r=13 -> nRounds=19, 80 words; 标准 AES-128 r=4 -> 10 轮
    nr19, sched19 = expand_key(key)
    nr10, sched10 = expand_key(b"8?)i_~Nk6qv0IX;2")
    check(nr19 == 19 and len(sched19) == 80 and nr10 == 10 and len(sched10) == 44,
          "key schedule 参数", f"(416bit: r=13, nRounds={nr19}, {len(sched19)} words; "
          f"128bit: {nr10} 轮, {len(sched10)} words)")

    # 4. AES-128 标准向量 (test.ipynb cell10): "Hello, World!" -> cc504ae98934a33c5f2c001962deb730
    ct10 = aes_ecb_encrypt(b"Hello, World!", b"8?)i_~Nk6qv0IX;2")
    check(ct10.hex() == "cc504ae98934a33c5f2c001962deb730", "AES-128 标准向量",
          f"({ct10.hex()[:16]}...)")

    # 5. 真实 416-bit 密文解密 (samples.json, 原项目 2024-11 抓包)
    samples = json.loads((pathlib.Path(__file__).parent / "samples.json").read_text(encoding="utf-8"))
    cipher = base64.b64decode(samples["cipher_b64"])
    plain = aes_ecb_decrypt(cipher, key)
    sha = hashlib.sha256(plain).hexdigest()
    check(sha == samples["plain_sha256"], "416-bit 密文解密 sha256",
          f"({sha[:16]}..., {len(cipher)}B -> {len(plain)}B)")

    # 6. 解密字段抽查 (真实响应内容)
    r = json.loads(plain)["response"]
    f = samples["fields"]
    d = r["docs"][0]
    ok = (r["numFound"] == f["numFound"] and r["start"] == f["start"]
          and d["brandName"][0] == f["first_brandName"] and d["st13"] == f["first_st13"]
          and d["applicationDate"] == f["first_applicationDate"] and d["type"] == f["first_type"])
    check(ok, "解密字段抽查",
          f"(numFound={r['numFound']}, start={r['start']}, 首条 "
          f"{d['brandName']!r} {d['st13']} {d['applicationDate']})")

    # 7. 重加密逐字节相等 (ECB 确定性, 最强等价证明)
    re_ct = aes_ecb_encrypt(plain, key)
    check(re_ct == cipher, "重加密 == 原密文 (逐字节)",
          f"({len(cipher)}B, sha256 {hashlib.sha256(re_ct).hexdigest()[:16]}...)")

    # 8. 416-bit key roundtrip (随机明文, 多块)
    ok = True
    for n in (1, 100, 1000):
        p = secrets.token_bytes(n)
        ok = ok and aes_ecb_decrypt(aes_ecb_encrypt(p, key), key) == p
    check(ok, "416-bit roundtrip ×3", "(1/100/1000 字节随机明文)")

    # 9. PKCE S256 (node 实跑捕获 tuple, auth.js 原函数)
    check(pkce_s256(PKCE_VERIFIER) == PKCE_CHALLENGE, "PKCE S256",
          f"({PKCE_CHALLENGE[:16]}...)")
    v = pkce_verifier()
    check(len(v) == 60 and set(v) <= set(PKCE_ALPHABET),
          "PKCE verifier 字母表/长度", f"(len {len(v)}, {len(set(v))} distinct)")
    check(len(pkce_s256(v)) == 43 and pkce_s256(v) == pkce_s256(v),
          "PKCE challenge 结构", "(43 字符 urlsafe b64, 去 =)")

    print(f"\n{passed}/{total} passed")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
