"""
雪球网 (xueqiu.com) — md5__1038 WAF 签名参数加密

用法:
    python main.py          # 运行全部样例验证 (纯标准库, 无需网络)
    python main.py --node   # 追加 Node 交叉验证 (需本机 node + 同目录 md1038_generator.js)

原理 (2026-08 新版, salt = 222029ad07):
    每个 API 请求 URL 需带 md5__1038, 格式 "<salt>-<LZW压缩编码>":
        mp   = encodeURIComponent(wafToken + method + salt + api_path)   # 注意: 全字符编码, 含 '=' 和 '/'
        mu   = mp + encodeURIComponent(fingerprint)
        mc1  = m4(m2(mu))    # m2 = SHA1[10:26] 截取 16 hex; m4 = 每 2 hex 与随机 0x2X 异或
        mc2  = m4(m2(mp))
        mc3  = F()           # 环境 bit 打包 (Fisher-Yates 洗牌后打包为整数)
        mc4  = 当前毫秒时间戳
        mc7  = XR(随机数|ms)哈希 + "a" + hex(ms)   # XR = p3*31+ord 的 32 位字符串哈希
        mc   = "mc1|mc2|mc3|mc4|wafToken|serverTs|mc7"
        token = salt + "-" + lzw_encode(mc)
    LZW: 字典 = 字符表 65 字符->0..64, 其余 chr(i)->65+i, 新词条从 321 递增;
         码宽从 9bit 动态扩容 (每写 512 个码字 +1bit); 码流按 6bit 打包映射回字符表。
    服务端 decode 后校验 mc1/mc2 (绑定 wafToken+请求+指纹) 与 wafToken/serverTs 回显。

样例来源: 2026-08 抓包 (3-补环境方案/e2e 日志: wafToken 0M6LZ... / serverTs 1782267246163)
归档来源: 经典 不开源/雪球网-md5__1038-WAF签名-2026-08-16 (本项目补全其未完成的纯算实现)
交叉验证: m2 + 3 组完整 token 与 md1038_generator.js 逐字节一致 (--node, 固定随机/时间)
"""

import hashlib
import json
import math
import random
import time
import urllib.parse

# 自定义 6-bit 字符表 (65 字符, 自 webpack bundle 提取)
_CHAR_TABLE = "g_GTtAIr2=sVcC6wvxopuSQYWbjFl5O3P7qeZakJBLiyXd8z/f4U09HmKRMhEDNn1"
_HEX = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F"]
SALT = "222029ad07"

# 真实抓包样例 (2026-08)
WAF_TOKEN = "0M6LZHCaMfDoej3MVMsyg2FZnPDn8VxE9GmBx7L0cE0="
SERVER_TS = "1782267246163"
API_PATH = "xueqiu.com/statuses/fundx/public/list.json"
DEFAULT_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36")


# ============================================================ 基础函数

def sha1_encrypt(msg: str) -> str:
    """标准 SHA1 (浏览器 unescape(encodeURIComponent()) = UTF-8 字节)"""
    return hashlib.sha1(msg.encode("utf-8")).hexdigest().lower()


def _encode_uri_component(s: str) -> str:
    """镜像 JS encodeURIComponent: 额外保留 ! ' ( ) * (urllib.quote 默认会编码)。"""
    return urllib.parse.quote(s, safe="!'()*-._~")


def m2(mm: str) -> str:
    """SHA1 摘要截取 [10:26] (16 个 hex 字符)"""
    return sha1_encrypt(mm)[10:26]


def m4(mm: str, rng=random) -> str:
    """每 2 个 hex 字符与随机字节异或; 随机字节高 4 位固定 2 (0x20-0x2F)"""
    result = []
    for i in range(0, len(mm), 2):
        mN = int(mm[i:i + 2], 16)
        mB = int("2" + _HEX[int(rng.random() * 16)], 16)
        result.append(f"{mN ^ mB:02x}")
    return "".join(result).lower()


def F(rng=random, now_ms=None) -> int:
    """环境标记: 17 个 0 + 随机/固定/时间 bit, Fisher-Yates 洗牌后打包为整数"""
    if now_ms is None:
        now_ms = int(time.time() * 1000)
    mm = [0] * 17
    mm.append(1 if rng.random() > 0.5 else 0)
    mm.append(1)
    mm.append(int(now_ms // 1000) % 2)
    mm.append(1 if rng.random() > 0.5 else 0)
    mm.extend([0, 0, 0, 1, 0, 0, 0, 1])
    for i in range(len(mm) - 1, -1, -1):          # 与 JS 一致: i 到 0 (自交换也消耗随机)
        j = int(rng.random() * (i + 1))
        mm[i], mm[j] = mm[j], mm[i]
    result = 0
    for i, bit in enumerate(mm):
        if bit:
            result |= (1 << i)
    return result


def XR(p0: str, p1: int = 0, p2: int = 1) -> int:
    """非密码学字符串哈希: p3 = p3 * 31 + ord(c), 32 位截断"""
    p3, p4, p5, p6 = 0, p1, len(p0), p2 or 1
    while p4 < p5:
        p3 = (p3 << 5) - p3 + ord(p0[p4])
        p3 &= 0xFFFFFFFF
        p4 += p6
    return p3


def mc7_generator(rng=random, now_ms=None) -> str:
    """mc7 = quote(XR(random|ms) + 'a' + hex(ms))"""
    xx = int(time.time() * 1000) if now_ms is None else now_ms
    random_num = int(4294967295 * rng.random()) & 0xFFFFFFFF
    p1 = f"{XR(f'{random_num}|{xx}')}a{xx:x}"
    return urllib.parse.quote(p1)


def build_fingerprint(opts: dict = None) -> str:
    """浏览器指纹: ua###platform###sw###sh###sw###sh###colorDepth###1###cores###memory"""
    opts = opts or {}
    return "###".join([
        opts.get("ua", DEFAULT_UA),
        opts.get("platform", "Win32"),
        str(opts.get("screenWidth", 1920)), str(opts.get("screenHeight", 1080)),
        str(opts.get("screenWidth", 1920)), str(opts.get("screenHeight", 1080)),
        str(opts.get("colorDepth", 24)), "1",
        str(opts.get("hardwareConcurrency", 8)),
        str(opts.get("deviceMemory", 8)),
    ])


# ============================================================ LZW 压缩 (自定义)

def lzw_encode(input_str: str) -> str:
    """LZW 压缩 + 6-bit 打包映射到字符表 (与原 JS LZW() 逐位一致)"""
    d = {}
    table_len = len(_CHAR_TABLE)
    next_code = 256 + table_len
    code_bits = 9
    code_counter = int(math.pow(2, code_bits))
    for i, ch in enumerate(_CHAR_TABLE):
        d[ch] = i
    for i in range(256):
        ch = chr(i)
        if ch not in d:
            d[ch] = table_len + i

    w, bit_buffer, bit_count, result = "", 0, 0, []

    def flush_code(code):
        nonlocal bit_buffer, bit_count, code_bits, code_counter
        for b in range(code_bits - 1, -1, -1):
            bit_buffer = (bit_buffer << 1) | ((code >> b) & 1)
            bit_count += 1
            if bit_count == 6:
                result.append(_CHAR_TABLE[bit_buffer])
                bit_buffer, bit_count = 0, 0
        code_counter -= 1
        if code_counter <= 0:
            code_bits += 1
            code_counter = int(math.pow(2, code_bits))

    for c in input_str:
        wc = w + c
        if wc in d:
            w = wc
        else:
            flush_code(d[w])
            d[wc] = next_code
            next_code += 1
            w = c
    if w != "":
        flush_code(d[w])
    if bit_count > 0:
        bit_buffer = bit_buffer << (6 - bit_count)
        result.append(_CHAR_TABLE[bit_buffer])
    return "".join(result)


def lzw_decode(encoded: str) -> str:
    """lzw_encode 的镜像解码器 (原 JS 无解码器, 按编码器语义手写还原)"""
    if not encoded:
        return ""
    table_len = len(_CHAR_TABLE)
    idx = {ch: i for i, ch in enumerate(_CHAR_TABLE)}
    bits = []
    for ch in encoded:
        v = idx[ch]
        for b in range(5, -1, -1):
            bits.append((v >> b) & 1)

    d = {}
    for i, ch in enumerate(_CHAR_TABLE):
        d[i] = ch
    for i in range(256):
        d[table_len + i] = chr(i)
    next_code = 256 + table_len
    code_bits, code_counter = 9, 512
    bit_pos = 0

    def read_code():
        nonlocal bit_pos, code_bits, code_counter
        c = 0
        for _ in range(code_bits):
            c = (c << 1) | bits[bit_pos]
            bit_pos += 1
        code_counter -= 1
        if code_counter <= 0:
            code_bits += 1
            code_counter = int(math.pow(2, code_bits))
        return c

    out = []
    prev = read_code()
    out.append(d[prev])
    while bit_pos + code_bits <= len(bits):
        code = read_code()
        if code in d:
            s = d[code]
        elif code == next_code:            # KwKwK: 新词条 == 上词条 + 首字符
            s = d[prev] + d[prev][0]
        else:
            break
        out.append(s)
        d[next_code] = d[prev] + s[0]
        next_code += 1
        prev = code
    return "".join(out)


# ============================================================ 主流程

def generate_md5_1038(waf_token: str, server_ts: str, api_path: str,
                      method: str = "get", salt: str = SALT,
                      fingerprint_opts: dict = None, rng=None,
                      now_ms: int = None) -> str:
    """生成 md5__1038 签名: salt + "-" + LZW(mc)

    rng / now_ms 仅用于确定性验证; 生产不传即用 random 与当前时间。
    """
    rng = rng or random
    if now_ms is None:
        now_ms = int(time.time() * 1000)
    fingerprint = build_fingerprint(fingerprint_opts or {})
    # 注意: encodeURIComponent 语义 (保留 !'()*), 不能直接用 quote(safe="")
    mp = _encode_uri_component(waf_token + method + salt + api_path)
    mu = mp + _encode_uri_component(fingerprint)

    mc = "|".join([
        m4(m2(mu), rng),                # mc1: 绑定请求 + 指纹
        m4(m2(mp), rng),                # mc2: 只绑定请求
        str(F(rng, now_ms)),            # mc3
        str(now_ms),                    # mc4
        waf_token,                      # 原样回显
        server_ts,                      # 原样回显
        mc7_generator(rng, now_ms),     # mc7
    ])
    return salt + "-" + lzw_encode(mc)


class SeqRng:
    """确定性随机序列（与 Node 侧 Math.random 覆盖逐值对齐）。"""

    def __init__(self, seq):
        self.seq = list(seq)
        self.calls = 0

    def random(self) -> float:
        v = self.seq[self.calls % len(self.seq)]
        self.calls += 1
        return v


def _seq(a: int, b: int, m: int, n: int = 48) -> list:
    """生成确定性随机序列: ((i*a+b) % m) / m (共 48 次: m4x16 + Fx31 + mc7x1)。"""
    return [((i * a + b) % m) / m for i in range(n)]


# 确定性向量: (waf_token, server_ts, api_path, method, now_ms, (a,b,m), expected)
# 随机序列/时间固定, 期望值由 reference/node_deterministic.js 生成并逐字节核对;
# waf_token/server_ts 为已过期测试值, 不可用于真实请求。
SAMPLE_CASES = [
    (WAF_TOKEN, SERVER_TS, API_PATH, "get", 1788025000123, (73, 11, 97),
     "222029ad07-t20A/aT23IP2TB6t25_P62g0YBaIPf_/4IaptBeI2bA/cTB8YB2Xv8TK6i_gt28A9rTdYI7g_g3YB0rv6A2ZI/CtBMI2DGveTv3rvVrvsAWg_gFtPntgDrK8_WxrP9gvmAgxt2LIPcrP0_sDdg8XSs_g4L/68SI_HaLK0_/9tLgiv4tW9A9dT2b"),
    (WAF_TOKEN, SERVER_TS, API_PATH + "?source=fund_public&page=1", "get",
     1788036000456, (41, 7, 101),
     "222029ad07-IvcALgtBbTB5I24_g5_/3BMD_PfAB3tW7IPdIB0A/eTBatB8YB4t252g4IB6YLgt28A/0TK6IafIScYB0rv6A2ZI/CtBMI2DGveTv3rvVrvsAWg_gFtPntgDrK8_WxrP9gvmAgxt2LIPcrP0_CLdW2_g6t22Iv62ACYd6TK3IP99IktdtIP4L20_ga_P8"),
    ("EXPIRED_TEST_TOKEN_0000000000000000000000000000=", "1700000000000",
     API_PATH, "get", 1788047000789, (89, 3, 103),
     "222029ad07-2gfIB9AB8t5rtW8_g2tW9tjDt2fT28ABcIP6tBfA/3_/7_fgYB4_AOA/0IqD2g7A9aIv7X/0dv9YBEAPPg/RrPDg2TrPSg5hT/KrPNgCz/HrfI=dK=dA8fSkYB2Iv04SaIP32gaU20IvfL6lAB5"),
]


def parse_md5_1038(token: str) -> dict:
    """解析签名: 还原 mc 并拆分 7 个字段 (服务端校验逻辑的镜像)"""
    salt, payload = token.split("-", 1)
    mc = lzw_decode(payload)
    fields = mc.split("|")
    if len(fields) != 7:
        raise ValueError(f"mc fields = {len(fields)}, expected 7")
    return {"salt": salt, "mc1": fields[0], "mc2": fields[1], "mc3": fields[2],
            "mc4": fields[3], "waf_token": fields[4], "server_ts": fields[5],
            "mc7": fields[6]}


# ============================================================ 样例验证

def main() -> None:
    passed = 0
    total = 0

    def check(ok: bool, label: str, detail: str = "") -> None:
        nonlocal passed, total
        total += 1
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label} {detail}")

    # 1. m2 确定性验证 (无随机, 期望值内嵌, 与 Node 交叉验证一致)
    mp1 = _encode_uri_component(WAF_TOKEN + "get" + SALT + API_PATH + "?source=fund_public&page=1")
    mp2 = _encode_uri_component(WAF_TOKEN + "get" + SALT + API_PATH)
    mu1 = mp1 + _encode_uri_component(build_fingerprint())
    for name, src, expect in [
        ("m2(mp real api)", mp2, "82d86a298cd5a67e"),
        ("m2(mp page=1)  ", mp1, "eaf8c525bfab768a"),
        ("m2(mu +fp)     ", mu1, "6df68571df044b7b"),
    ]:
        check(m2(src) == expect, name, f"-> {m2(src)} (expect {expect})")

    # 2. LZW roundtrip (编码->解码还原; 覆盖 KwKwK 分支)
    mc_samples = [
        "4f326a7fee2e9080|13393e0836b901dc|50724996|1787151421232|" +
        WAF_TOKEN + "|" + SERVER_TS + "|1a01a868f30",
        "abababababababababababababababab",                       # KwKwK: code == next_code
        "0123456789|abcdef|{}[]<>|~!@#$%^&*()_+",
    ]
    for i, s in enumerate(mc_samples):
        enc = lzw_encode(s)
        check(lzw_decode(enc) == s, f"lzw roundtrip #{i}", f"(len {len(s)} -> {len(enc)})")

    # 3. 确定性向量: 固定随机序列/时间, 与 Node 侧逐字节一致
    for i, (tok_in, ts, api, method, now_ms, (a, b, m), expected) in enumerate(
            SAMPLE_CASES, 1):
        got = generate_md5_1038(tok_in, ts, api, method=method,
                                rng=SeqRng(_seq(a, b, m)), now_ms=now_ms)
        ok = got == expected
        detail = f"(len {len(got)})"
        if ok:
            p = parse_md5_1038(got)
            ok = (p["salt"] == SALT and p["waf_token"] == tok_in
                  and p["server_ts"] == ts and p["mc4"] == str(now_ms)
                  and len(p["mc1"]) == 16 and len(p["mc2"]) == 16)
        check(ok, f"vector #{i} exact match", detail)

    # 4. 随机路线: 相同输入两次生成不同, 但结构合法
    t1 = generate_md5_1038(WAF_TOKEN, SERVER_TS, API_PATH)
    t2 = generate_md5_1038(WAF_TOKEN, SERVER_TS, API_PATH)
    try:
        ok = t1 != t2 and parse_md5_1038(t1)["waf_token"] == WAF_TOKEN
    except ValueError:
        ok = False
    check(ok, "randomized", "(same input -> different token)")

    # 5. 可选 Node 交叉验证: 同序列/时间下两边逐字节一致
    import os
    import subprocess
    here = os.path.dirname(os.path.abspath(__file__))
    js_path = os.path.join(here, "md1038_generator.js")
    node_ref = os.path.join(here, "reference", "node_deterministic.js")
    if "--node" in os.sys.argv and os.path.exists(js_path) and os.path.exists(node_ref):
        for i, (tok_in, ts, api, method, now_ms, (a, b, m), expected) in enumerate(
                SAMPLE_CASES, 1):
            try:
                out = subprocess.run(
                    ["node", node_ref, tok_in, ts, api, method,
                     str(now_ms), str(a), str(b), str(m), "48"],
                    capture_output=True, text=True, timeout=30, check=True)
                node_token = json.loads(out.stdout.strip())["token"]
                check(node_token == expected, f"node vector #{i}",
                      "(JS == PY, 48 random calls)")
            except Exception as e:
                check(False, f"node vector #{i}", f"({e})")
    else:
        print("[SKIP] node cross-check (--node flag or node files missing)")

    print(f"\n{passed}/{total} passed")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
