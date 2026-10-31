# -*- coding: utf-8 -*-
"""
今日头条 a_bogus 纯算法实现（标准库，零 Node 依赖）

签名结构（2026-09-02 全链还原，线上 5/5）:

    inner    = UA XOR RC4(b'\\x00\\x09\\x0e')                # 内层 111B
    h_query  = be_sum(be_sum(query + 'cus'))                # 双重自研哈希
    h_cus    = be_sum(be_sum('cus'))
    h_inner  = be_sum(b64_s3(inner))
    stream44 = [44, 时间/score/pageId/aid/ink 拆字节 + 哈希字节...]
    checksum = XOR(stream44 按反汇编顺序)
    tail55   = DIMS + '|Win32' 字符码 + [checksum]
    body99   = (stream44 + tail55) XOR RC4(b'y')
    sig      = base64(head12 + body99, S4 字母表)            # 148 字符

    head12 服务端不校验；ink = 签名时刻，服务端校验约 30 秒新鲜度。

运行:
    py main.py           # 离线：be_sum/RC4 组件 + 3 组确定性向量
    py main.py --node    # 追加：旧版 Node 补环境路线（164/168/172 字符 + msToken）
    py main.py --live    # 追加：纯算法生成 → 真实 feed 请求（需网络）
"""

import json
import os
import subprocess
import sys
import time
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SIGN_JS = os.path.join(BASE_DIR, "toutiao_sign.js")

S4_ALPHA = "Dkdpgh2ZmsQB80/MfvV36XI1R45-WUAlEixNLwoqYTOPuzKFjJnry79HbGcaStCe"
S3_ALPHA = "ckdp1h4ZKsUB80/Mfvw36XIgR25+WQAlEi7NLboqYTOPuzmFjJnryx9HVGDaStCe"
MASK = 0xFFFFFFFF
H0 = [1937774191, 1226093241, 388252375, 3666478592,
      2842636476, 372324522, 3817729613, 2969243214]

UA_DEFAULT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36")
DIMS = "0|0|1440|810|0|0|0|0|1440|810|1440|810|0|0|24|24"   # 窗口 16 键
PLATFORM = "Win32"
PAGE_ID, AID = 6457, 24
SIG_CHARS = set(S4_ALPHA)


# ---------- 自研哈希 be_sum（SHA-256 骨架 + 深度定制） ----------

def _rotl(x, n):
    n %= 32
    return ((x << n) | (x >> (32 - n))) & MASK


def _be_sum(data):
    """两段式 sum 链：轮常数 0x79CC4519/0x7A879D8A 且每轮 rotL(K,f)；
    前半 a^b^c、后半 majority/Ch；c=rotL(b,9)、g=rotL(f,19)、T2 三重 XOR；
    状态合并 XOR；消息调度 68 项 + w'[a]=w[a]^w[a+4]。"""
    if isinstance(data, str):
        data = data.encode("utf-8")
    reg = list(H0)

    def compress(t):
        w = [0] * 132
        for a in range(16):
            e = t[4 * a:4 * a + 4]
            w[a] = (((e[0] if len(e) > 0 else 0) << 24) |
                    ((e[1] if len(e) > 1 else 0) << 16) |
                    ((e[2] if len(e) > 2 else 0) << 8) |
                    (e[3] if len(e) > 3 else 0)) & MASK
        for a in range(16, 68):
            n = w[a - 16] ^ w[a - 9] ^ _rotl(w[a - 3], 15)
            n = n ^ _rotl(n, 15) ^ _rotl(n, 23)
            w[a] = (n ^ _rotl(w[a - 13], 7) ^ w[a - 6]) & MASK
        for a in range(64):
            w[a + 68] = (w[a] ^ w[a + 4]) & MASK
        st = list(reg)
        for f in range(64):
            K = 2043430169 if f < 16 else 2055708042
            o = _rotl((st[0] + 0) & MASK, 12) + st[4] + _rotl(K, f)
            o = _rotl(o & MASK, 7)
            s = (o ^ _rotl(st[0], 12)) & MASK
            if f < 16:
                u = ((st[0] ^ st[1] ^ st[2]) + st[3] + s + w[f + 68]) & MASK
                b = ((st[4] ^ st[5] ^ st[6]) + st[7] + o + w[f]) & MASK
            else:
                u = ((st[0] & st[1] | st[0] & st[2] | st[1] & st[2])
                     + st[3] + s + w[f + 68]) & MASK
                b = ((st[4] & st[5] | (~st[4] & st[6]))
                     + st[7] + o + w[f]) & MASK
            st[3], st[2], st[1], st[0] = st[2], _rotl(st[1], 9), st[0], u
            st[7], st[6], st[5] = st[6], _rotl(st[5], 19), st[4]
            st[4] = (b ^ _rotl(b, 9) ^ _rotl(b, 17)) & MASK
        for d in range(8):
            reg[d] = (reg[d] ^ st[d]) & MASK

    i = 0
    size = len(data)
    while i + 64 <= size:
        compress(data[i:i + 64])
        i += 64
    chunk = bytearray(data[i:])
    chunk.append(0x80)
    c = len(chunk) % 64
    if 64 - c < 8:
        c -= 64
    while c < 56:
        chunk.append(0)
        c += 1
    n = 8 * size
    hi = n // 4294967296
    for k in range(4):
        chunk.append((hi >> (8 * (3 - k))) & 255)
    for k in range(4):
        chunk.append((n >> (8 * (3 - k))) & 255)
    for i in range(0, len(chunk), 64):
        compress(chunk[i:i + 64])
    out = bytearray(32)
    for i in range(8):
        o = reg[i] & MASK
        out[4 * i + 3] = o & 255
        out[4 * i + 2] = (o >> 8) & 255
        out[4 * i + 1] = (o >> 16) & 255
        out[4 * i] = (o >> 24) & 255
    return bytes(out)


# ---------- RC4 / 自定义 base64 ----------

def _rc4(key, n):
    s = list(range(256))
    j = 0
    for i in range(256):
        j = (j + s[i] + key[i % len(key)]) % 256
        s[i], s[j] = s[j], s[i]
    i = j = 0
    out = bytearray()
    for _ in range(n):
        i = (i + 1) % 256
        j = (j + s[i]) % 256
        s[i], s[j] = s[j], s[i]
        out.append(s[(s[i] + s[j]) % 256])
    return bytes(out)


def _b64(data, alpha=S4_ALPHA):
    out = []
    for i in range(0, len(data), 3):
        b = data[i:i + 3]
        v = (b[0] << 16) | ((b[1] if len(b) > 1 else 0) << 8) | (b[2] if len(b) > 2 else 0)
        out.append(alpha[(v >> 18) & 63])
        out.append(alpha[(v >> 12) & 63])
        out.append(alpha[(v >> 6) & 63] if len(b) > 1 else "=")
        out.append(alpha[v & 63] if len(b) > 2 else "=")
    return "".join(out)


# ---------- 签名入口 ----------

def abogus(query, ua=UA_DEFAULT, now_ms=None, score=9, head=None):
    """生成 a_bogus（148 字符）。query = URL 参数串（不含 a_bogus）。"""
    if now_ms is None:
        now_ms = int(time.time() * 1000)
    ink = now_ms

    # 1) 内层: UA XOR RC4([0, 9, 14])
    k_inner = _rc4(bytes([0, 9, 14]), len(ua))
    inner = bytes(ord(c) ^ k_inner[i] for i, c in enumerate(ua))

    # 2) 三重哈希（query/cus 均为双重 sum）
    h_query = _be_sum(_be_sum(query + "cus"))
    h_cus = _be_sum(_be_sum("cus"))
    h_inner = _be_sum(_b64(inner, S3_ALPHA).encode())

    # 3) 44 值流（fromCharCode 参数顺序）
    s = [
        44, (now_ms >> 24) & 255, 0, (score >> 24) & 255, 0, 0, 0,
        h_query[21], h_cus[21], 0, h_inner[23], (now_ms >> 16) & 255,
        (score >> 16) & 255, (PAGE_ID >> 8) & 255, PAGE_ID & 255,
        score & 255, 0, AID & 255, h_query[22], h_cus[22], h_inner[24],
        (now_ms >> 8) & 255, (score >> 8) & 255, 0, 0, 0,
        now_ms & 255, (score >> 24) & 255, 0, 14,
        (ink >> 24) & 255, (ink >> 16) & 255, 0, (ink >> 8) & 255, ink & 255,
        3, ink // 2 ** 32, ink // 2 ** 40,
        now_ms // 2 ** 32, now_ms // 2 ** 40, 54, 0, 0, 0,
    ]

    # 4) checksum：按反汇编顺序 XOR（漏一项 = 单字节差 = 拒收）
    x = 0
    for v in [s[0], s[1], s[3], s[4], s[5], s[7], s[8], s[10], s[11], s[12],
              s[15], s[16], s[18], s[19], s[20], s[21], s[22], s[23], s[25],
              s[26], s[27], s[28], s[29], s[30], s[31], s[32], s[33], s[34], 3,
              s[36], s[37], s[38], s[39], 0, 0, s[13], s[14], s[17], 0, 0, 0,
              54, 0, 0, 0]:
        x ^= v

    # 5) tail55 + 6) body99 XOR RC4('y')
    tail = list((DIMS + "|" + PLATFORM).encode()) + [x & 255]
    raw99 = s + tail
    k = _rc4(b"y", len(raw99))
    body = bytes((v ^ k[i]) & 255 for i, v in enumerate(raw99))

    # 7) head12（服务端不校验）+ 自定义 base64
    if head is None:
        head = bytes([0x2B, 0x53, 0x07, 0x3D, 0x83, 0x00, 0x00,
                      0x11, 0x09, 0x44, 0x25, 0x03])
    return _b64(head + body, S4_ALPHA)


# ---------- 备份路线：旧版 Node 补环境（toutiao_sign.js） ----------

def node_signature(params_str):
    """node toutiao_sign.js "<params>" -> {a_bogus, msToken}。"""
    result = subprocess.run(
        ["node", SIGN_JS, params_str],
        capture_output=True, text=True, timeout=60, cwd=BASE_DIR,
    )
    if result.returncode != 0:
        raise RuntimeError("Node 签名失败: %s" % result.stderr[-400:])
    return json.loads(result.stdout.strip().splitlines()[-1])


NODE_CASES = [
    ("channel_id=0&max_behot_time=0&category=pc_profile_recommend&aid=24&app_name=toutiao_web",
     {164, 168, 172}, 120),
    ("offset=0&channel_id=94349549395&max_behot_time=0&category=pc_profile_channel"
     "&disable_raw_data=true&aid=24&app_name=toutiao_web", {164, 168, 172}, 120),
    ("offset=0&channel_id=3189398996&max_behot_time=1725964720&aid=24&app_name=toutiao_web",
     {164, 168, 172}, 120),
]


# ---------- 样例 ----------
# (query, now_ms, expected) — 由经典纯算法（2026-09-02 线上 5/5）固定时间生成
SAMPLE_CASES = [
    ("channel_id=0&max_behot_time=1788312759&offset=0&category=pc_profile_recommend"
     "&aid=24&app_name=toutiao_web", 1788312759000,
     "Q78ZMR8DDkgsvd6p5UKLfY3qVWr3Yml80t9b0Dhqtn3QHg39HMPR9exon/vvhhujFs/jIbyjy4hGapPME5Qy01w4HWDKUdQZ-g00t-PZ-oWSs1Jnejusn0vNmk4ASaBQsvV3EQDkqXMH9U0lA2LP"),
    ("channel_id=0&max_behot_time=1788320000&offset=20&category=pc_profile_recommend"
     "&aid=24&app_name=toutiao_web", 1788320000123,
     "Q78ZMR8DDkgsvd6p5AVLfY3qV5q3YmUA0t9b0DhqLV3Q1L39HMTa9exotH4vwFEjFs/jIbyjy4hGapPME5Qy01w4HWDKUdQZ-g00t-PZ-oWSs1Jnejusn0vNmk4ASaBQsvV3EQDkqXMH9U0lA2LY"),
    ("offset=0&channel_id=94349549395&max_behot_time=0&category=pc_profile_channel"
     "&disable_raw_data=true&aid=24&app_name=toutiao_web", 1788333333456,
     "Q78ZMR8DDkgsvd6p5AVLfY3qVUZ3YmAQ0t9b0Dhqod3Qa639HMPf9exotcsvsX8jFs/jIbyjy4hGapPME5Qy01w4HWDKUdQZ-g00t-PZ-oWSs1Jnejusn0vNmk4ASaBQsvV3EQDkqXMH9U0lA2w4"),
]


def live_request(now_ms=None):
    """纯算法签名 + 裸 urllib 请求 feed（签名需 30 秒内发出）。"""
    now_ms = now_ms or int(time.time() * 1000)
    query = ("channel_id=0&max_behot_time=%d&offset=0"
             "&category=pc_profile_recommend&aid=24&app_name=toutiao_web"
             % (now_ms // 1000))
    sig = abogus(query, now_ms=now_ms)
    url = "https://www.toutiao.com/api/pc/list/feed?" + query + "&a_bogus=" + sig
    req = urllib.request.Request(url, headers={
        "User-Agent": UA_DEFAULT,
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read()
        return resp.status, b'"success"' in body, len(body)


# ---------- 主流程 ----------

def main():
    passed, total = 0, 0

    def check(ok, label, detail=""):
        nonlocal passed, total
        total += 1
        passed += ok
        print("[%s] %s %s" % ("PASS" if ok else "FAIL", label, detail))

    # 1. 组件向量（经典项目 JS 侧验证值）
    check(_be_sum("cus").hex() ==
          "417d9419cff0742bacd41b07de88334d86546560873f7912a6adcbe82b8161bf",
          "be_sum('cus')", "(32B)")
    check(_be_sum(_be_sum("cus")).hex() ==
          "886572933a4dcfc9d7a29a5df80d8ea06949d7f1533a332bff26a88dd8c223ec",
          "be_sum(be_sum('cus'))", "(double sum)")
    check(_rc4(b"Key", 9).hex() == "eb9f7781b734ca72a7",
          "RC4 standard vector", "(Key/Plaintext keystream)")

    # 2. 确定性向量：逐字节比对 + 长度/字符集
    for i, (query, now_ms, expected) in enumerate(SAMPLE_CASES, 1):
        got = abogus(query, now_ms=now_ms)
        ok = (got == expected and len(got) == 148
              and all(c in SIG_CHARS for c in got))
        check(ok, "vector #%d exact match" % i,
              "(%d chars, head %s)" % (len(got), got[:12]))

    # 3. 时间敏感：同 query 不同 now → 不同签名；重复调用稳定
    a1 = abogus(SAMPLE_CASES[0][0], now_ms=1788312759000)
    a2 = abogus(SAMPLE_CASES[0][0], now_ms=1788312760000)
    check(a1 == SAMPLE_CASES[0][2] and a2 != a1,
          "time sensitivity", "(1s shift changes signature)")

    # 4. 备份路线：旧版 Node 补环境（--node）
    if "--node" in sys.argv:
        for i, (params, lens, ms_len) in enumerate(NODE_CASES, 1):
            try:
                sig = node_signature(params)
                a_bogus, ms_token = sig["a_bogus"], sig["msToken"]
                ok = (len(a_bogus) in lens and len(ms_token) == ms_len)
                detail = "(a_bogus %d, msToken %d)" % (len(a_bogus), len(ms_token))
            except Exception as exc:            # noqa: BLE001 - 备份路线
                ok, detail = False, "(%s)" % exc
            check(ok, "node backup #%d" % i, detail)
    else:
        print("[SKIP] --node backup route (add --node, needs node)")

    # 5. 真实请求（--live，纯算法）
    if "--live" in sys.argv:
        status, success, size = live_request()
        check(status == 200 and success, "live feed request",
              "(HTTP %d, success=%s, %d bytes)" % (status, success, size))
    else:
        print("[SKIP] --live real request (add --live, needs network)")

    print("\n%d/%d passed" % (passed, total))
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
