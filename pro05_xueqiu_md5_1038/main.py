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
交叉验证: m2 期望值与 md1038_generator.js (Node) 逐值一致
"""

import hashlib
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


def m2(mm: str) -> str:
    """SHA1 摘要截取 [10:26] (16 个 hex 字符)"""
    return sha1_encrypt(mm)[10:26]


def m4(mm: str) -> str:
    """每 2 个 hex 字符与随机字节异或; 随机字节高 4 位固定 2 (0x20-0x2F)"""
    result = []
    for i in range(0, len(mm), 2):
        mN = int(mm[i:i + 2], 16)
        mB = int("2" + _HEX[random.randint(0, 15)], 16)
        result.append(f"{mN ^ mB:02x}")
    return "".join(result).lower()


def F() -> int:
    """环境标记: 17 个 0 + 随机/固定/时间 bit, Fisher-Yates 洗牌后打包为整数"""
    mm = [0] * 17
    mm.append(1 if random.random() > 0.5 else 0)
    mm.append(1)
    mm.append(int(time.time()) % 2)
    mm.append(1 if random.random() > 0.5 else 0)
    mm.extend([0, 0, 0, 1, 0, 0, 0, 1])
    for i in range(len(mm) - 1, 0, -1):          # Fisher-Yates 洗牌
        j = random.randint(0, i)
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


def mc7_generator() -> str:
    """mc7 = quote(XR(random|ms) + 'a' + hex(ms))"""
    xx = int(time.time() * 1000)
    random_num = int(4294967295 * random.random()) & 0xFFFFFFFF
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
                      fingerprint_opts: dict = None) -> str:
    """生成 md5__1038 签名: salt + "-" + LZW(mc)"""
    fingerprint = build_fingerprint(fingerprint_opts or {})
    # 注意 safe='': 与 JS encodeURIComponent 一致 (编码 '=' 和 '/')
    mp = urllib.parse.quote(waf_token + method + salt + api_path, safe="")
    mu = mp + urllib.parse.quote(fingerprint, safe="")

    mc = "|".join([
        m4(m2(mu)),              # mc1: 绑定请求 + 指纹
        m4(m2(mp)),              # mc2: 只绑定请求
        str(F()),                # mc3
        str(int(time.time() * 1000)),  # mc4
        waf_token,               # 原样回显
        server_ts,               # 原样回显
        mc7_generator(),         # mc7
    ])
    return salt + "-" + lzw_encode(mc)


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
    mp1 = urllib.parse.quote(WAF_TOKEN + "get" + SALT + API_PATH + "?source=fund_public&page=1", safe="")
    mp2 = urllib.parse.quote(WAF_TOKEN + "get" + SALT + API_PATH, safe="")
    mu1 = mp1 + urllib.parse.quote(build_fingerprint(), safe="")
    for name, src, expect in [
        ("m2(mp real api)", mp2, "82d86a298cd5a67e"),
        ("m2(mp page=1)  ", mp1, "eaf8c525bfab768a"),
        ("m2(mu +fp)     ", mu1, "de1d2c8ddd78055f"),
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

    # 3. 完整签名结构 (随机算法, 结构验证)
    for i in range(2):
        tok = generate_md5_1038(WAF_TOKEN, SERVER_TS, API_PATH)
        try:
            p = parse_md5_1038(tok)
            ok = (p["salt"] == SALT
                  and p["waf_token"] == WAF_TOKEN
                  and p["server_ts"] == SERVER_TS
                  and len(p["mc1"]) == 16 and len(p["mc2"]) == 16
                  and abs(int(time.time() * 1000) - int(p["mc4"])) < 5000)
            check(ok, f"token structure #{i}", f"(len {len(tok)}, mc4={p['mc4']})")
        except ValueError as e:
            check(False, f"token structure #{i}", f"({e})")

    # 4. 可变性: 相同输入两次生成不同 (m4/F/mc7 含随机)
    t1 = generate_md5_1038(WAF_TOKEN, SERVER_TS, API_PATH)
    t2 = generate_md5_1038(WAF_TOKEN, SERVER_TS, API_PATH)
    check(t1 != t2, "randomized", "(same input -> different token)")

    # 5. 可选 Node 交叉验证: 本机有 node 且同目录有 md1038_generator.js
    import os
    import subprocess
    js_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "md1038_generator.js")
    if "--node" in os.sys.argv and os.path.exists(js_path):
        try:
            out = subprocess.run(
                ["node", "-e",
                 f"const XQW=require({js_path!r});"
                 f"console.log(XQW.md5_1038({WAF_TOKEN!r},{SERVER_TS!r},"
                 f"{{api:{API_PATH!r},method:'get',salt:{SALT!r}}}));"],
                capture_output=True, text=True, timeout=30, check=True)
            p = parse_md5_1038(out.stdout.strip())
            ok = (p["waf_token"] == WAF_TOKEN and p["server_ts"] == SERVER_TS
                  and p["salt"] == SALT and len(p["mc1"]) == 16)
            check(ok, "node cross-check", f"(node token decode -> mc structure)")
        except Exception as e:
            check(False, "node cross-check", f"({e})")
    else:
        print("[SKIP] node cross-check (--node flag or node/md1038_generator.js missing)")

    print(f"\n{passed}/{total} passed")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
