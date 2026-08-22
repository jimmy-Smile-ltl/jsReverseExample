"""
拉钩网 (www.lagou.com) — 职位搜索加密链: AES-256-CBC 请求/响应 + RSA-2048 保护 AES Key + X_HTTP_TOKEN

用法:
    python main.py   # 加密链验证: X-S-HEADER / X_HTTP_TOKEN / 请求加密 / 响应解密 (纯 Python, 无网络)

原理 (拉钩解码.js, 2024-07-17 原项目抓包; 期望值经真实 crypto-js+jsencrypt node 实跑交叉验证, 2026-08-20):
    1. AES Key: 32 字符随机串 (字母表 ABCD...+/=)
    2. RSA: JSEncrypt RSA-2048/PKCS1v1.5 加密 AES Key -> base64 (344 字符) -> POST gate.lagou.com/system/agreement 激活
    3. X-S-HEADER = jt(aesKey, originalData, url):
       t = SHA256( JSON.stringify({deviceType:1}) + url + JSON.stringify(originalData) ).toUpperCase()
       -> AES-256-CBC 加密 JSON{originHeader: JSON.stringify({deviceType:1}), code: t}
       (注: JS 里 url 为 undefined 时 concat 出字符串 "undefined", 测试样例原样保留了此行为)
    4. body = AES 加密 JSON.stringify(originalData); 响应 data 字段 AES 解密 -> 职位 JSON
    5. X_HTTP_TOKEN: md5 = MD5("HTTP_JS_KEY" + user_trace_token)
       token = reverse(md5[:16] + ts秒 + md5[16:32])   (ts = Math.floor(Date.now()/1000), 10 位整数)
    6. traceparent = "00-" + 32hex + "-" + 16hex + "-01"  (E(): Uint8Array(16) 随机 -> hex)

    AES: key=aesKey(32B), iv="c558Gq0YQK2QUlMc"(16B), CBC, Pkcs7, 输出 base64 (CryptoJS .toString())
    OB 字符串表: getXHttpToken 内 59 元素数组 shift 331 次 (331%59=36) 后, 表[0x4]="HTTP_JS_KEY",
                表[0x39]="user_trace_token", 表[0x36]=MD5 解密器; cookie 正则 (^|\x20)user_trace_token=([^;]*)(;|$)

样例来源: 拉钩解码.js 内嵌测试块 (encryptedData = 2024-07-17 真实响应密文) + node 实跑捕获.
"""

import base64
import hashlib
import json
import os
import re
import secrets
import sys

# pycryptodome (pip install pycryptodome)
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.PublicKey import RSA

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

# ---- 常量 (拉钩解码.js) ----
AES_IV = "c558Gq0YQK2QUlMc"
RSA_PUB = ("-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnbJqzIXk6qGotX5nD52"
           "1Vk/24APi2qx6C+2allfix8iAfUGqx0MK3GufsQcAt/o7NO8W+qw4HPE+RBR6m7+3JVlKA"
           "F5LwYkiUJN1dh4sTj03XQ0jsnd3BYVqL/gi8iC4YXJ3aU5VUsB6skROancZJAeq95p7eh"
           "XXAJfCbLwcK+yFFeRKLvhrjZOMDvh1TsMB4exfg+h2kNUI94zu8MK3UA7v1ANjfgopaE+"
           "cpvoulg446oKOkmigmc35lv8hh34upbMmehUqB51kqk9J7p8VMI3jTDBcMC21xq5XF7oM"
           "8gmqjNsYxrT9EVK7cezYPq7trqLX1fyWgtBtJZG7WMftKwIDAQAB\n-----END PUBLIC KEY-----")
KEY_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="

# 测试块固定输入 (拉钩解码.js 内嵌, 2024-07-17)
AES_KEY = "dgHY1qVeo/Z0yDaF5WV/EEXxYiwbr5Jt"
ORIGINAL_DATA = {"first": "true", "needAddtionalResult": "false",
                 "city": "全国", "pn": "2", "kd": "Java"}
COOKIE = "user_trace_token=20220307181843-924fc03b-fa6b-45bb-a4b1-7b9572b20b18"
REAL_URL = "https://www.lagou.com/jobs/v2/positionAjax.json"

# node 实跑交叉验证期望值 (原 JS + 真实 crypto-js/jsencrypt, 2026-08-20 捕获)
XS_UNDEF = ("NeeOlLq93FMl0Xzi79Fr4A3PQF57CqoaROkcM8N9wmMfEFlOpuMXAqaMXkur6W4Neae6yk4N5SXVaGGkqtJat"
            "+L4z9FzcE3GtfJrCSbSSf0doN4GJh4FtSV0Fjx40weTedOWcQaT1hy7ko6eos2wNg==")
XS_URL = ("NeeOlLq93FMl0Xzi79Fr4A3PQF57CqoaROkcM8N9wmObOO5NX9jHBlDi0n1nHeeBD2CSuhNqRXDUyET8I30SWh"
          "7AXIAou/Fmf0uIHReX4uts9YVyBDEB2yG3oCba3hYrjOjMH1bUM2Hcs4doHfjy6w==")
REQUEST_DATA = ("4vkQ2vHW22A7cVp2Z0Ke8gnpOAaW7X2hCN3hTMcpN/vlRh6hV+bDBgrbfr41L8BwORvCqwJCpnebFU3+kbqW"
                "TAPdiPtyQ74dS09Of3FkAe97LbN0DYoo6tD8jAiYB52I")
# node 实跑捕获: ts=1787157649 时 token=e5ab78d92f389422946751787106351df7c5441dab
TOKEN_TS = 1787157649
TOKEN_EXPECT = "e5ab78d92f389422946751787106351df7c5441dab"


def rt(plain: str, aes_key: str) -> str:
    """对应 Rt(): AES-256-CBC (iv 固定) + Pkcs7 -> base64 (CryptoJS .toString())"""
    raw = plain.encode("utf-8")
    pad = 16 - len(raw) % 16  # Pkcs7: 补 (16-len%16) 字节, 字节值 == 补位数
    padded = raw + bytes([pad]) * pad
    cipher = AES.new(aes_key.encode(), AES.MODE_CBC, AES_IV.encode()).encrypt(padded)
    return base64.b64encode(cipher).decode()


def it(cipher_b64: str, aes_key: str):
    """对应 It(): AES 解密 -> UTF-8; 若能 JSON.parse 则返回 dict"""
    ct = base64.b64decode(cipher_b64)
    plain = AES.new(aes_key.encode(), AES.MODE_CBC, AES_IV.encode()).decrypt(ct)
    plain = plain[:-plain[-1]]
    text = plain.decode("utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def jt(aes_key: str, original_data: dict, url: str) -> str:
    """对应 jt(): X-S-HEADER = AES(JSON{originHeader, code: SHA256 大写})"""
    origin = json.dumps({"deviceType": 1}, separators=(",", ":"))
    body = json.dumps(original_data, ensure_ascii=False, separators=(",", ":"))
    code = hashlib.sha256(f"{origin}{url}{body}".encode()).hexdigest().upper()
    return rt(json.dumps({"originHeader": origin, "code": code},
                         separators=(",", ":")), aes_key)


def get_request_data(aes_key: str, original_data: dict) -> str:
    """对应 getRequestData(): body = AES(JSON.stringify(originalData))"""
    return rt(json.dumps(original_data, ensure_ascii=False, separators=(",", ":")), aes_key)


def get_x_http_token(cookie: str, ts: int) -> str:
    """对应 getXHttpToken(): token = reverse(md5[:16] + ts + md5[16:32])

    user_trace_token 取 cookie 正则 (^|\\x20)user_trace_token=([^;]*)(;|$);
    ts = Math.floor(Date.now()/1000) 秒级时间戳 (10 位整数)。
    """
    m = re.search(r"(?:^| )user_trace_token=([^;]*)(?:;|$)", cookie)
    tok = m.group(1)
    md5 = hashlib.md5(f"HTTP_JS_KEY{tok}".encode()).hexdigest()
    return f"{md5[:16]}{ts}{md5[16:]}"[::-1]


def get_traceparent() -> str:
    """对应 getTraceparent(): "00-" + 32hex + "-" + 16hex + "-01" (E(16) 随机)"""
    return f"00-{secrets.token_hex(16)}-{secrets.token_hex(8)}-01"


def gen_aes_key() -> str:
    """对应 getAesKeyAndRsaEncryptData() 内: 32 字符取自 KEY_ALPHABET 的随机串"""
    return "".join(secrets.choice(KEY_ALPHABET) for _ in range(32))


def rsa_encrypt_aes_key(aes_key: str) -> str:
    """对应 JSEncrypt.encrypt(aesKey): RSA-2048/PKCS1v1.5 -> base64 (344 字符)"""
    pub = RSA.import_key(RSA_PUB)
    return base64.b64encode(PKCS1_v1_5.new(pub).encrypt(aes_key.encode())).decode()


def main() -> None:
    passed, total = 0, 0

    def check(ok: bool, label: str, detail: str = "") -> None:
        nonlocal passed, total
        total += 1
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label} {detail}")

    # 1. X-S-HEADER (测试块原样, u=undefined -> JS concat 出 "undefined")
    got = jt(AES_KEY, ORIGINAL_DATA, "undefined")
    check(got == XS_UNDEF, "X-S-HEADER u=undefined", f"({len(got)} b64 chars)")
    inner = it(got, AES_KEY)
    origin = json.dumps({"deviceType": 1}, separators=(",", ":"))
    body = json.dumps(ORIGINAL_DATA, ensure_ascii=False, separators=(",", ":"))
    code = hashlib.sha256(f"{origin}undefined{body}".encode()).hexdigest().upper()
    check(inner["originHeader"] == origin and inner["code"] == code,
          "X-S-HEADER inner code (SHA256+undefined 独立复算)",
          f"(code={inner['code'][:16]}...)")

    # 2. X-S-HEADER (真实请求 URL)
    got = jt(AES_KEY, ORIGINAL_DATA, REAL_URL)
    check(got == XS_URL, "X-S-HEADER real url", f"({len(got)} b64 chars)")
    inner = it(got, AES_KEY)
    code = hashlib.sha256(f"{origin}{REAL_URL}{body}".encode()).hexdigest().upper()
    check(inner["originHeader"] == origin and inner["code"] == code,
          "X-S-HEADER inner code (真实 url)", f"(code={inner['code'][:16]}...)")

    # 3. X_HTTP_TOKEN (固定 cookie + 固定 ts)
    got = get_x_http_token(COOKIE, TOKEN_TS)
    check(got == TOKEN_EXPECT, "X_HTTP_TOKEN fixed ts", f"({got[:8]}... len {len(got)})")
    md5 = hashlib.md5(b"HTTP_JS_KEY20220307181843-924fc03b-fa6b-45bb-a4b1-7b9572b20b18").hexdigest()
    r = got[::-1]
    check(r == f"{md5[:16]}{TOKEN_TS}{md5[16:]}",
          "X_HTTP_TOKEN reverse structure",
          f"(md5={md5[:8]}..., ts={TOKEN_TS})")
    # 从"实时" token 反向提取 ts 的可行性与首尾校验 (用另外两个 node 实跑值)
    for t2 in ("e5ab78d92f389422666751787106351df7c5441dab",
               "e5ab78d92f389422376751787106351df7c5441dab"):
        r2 = t2[::-1]
        ok = (r2.startswith(md5[:16]) and r2.endswith(md5[16:])
              and r2[16:26].isdigit())
        check(ok, "X_HTTP_TOKEN live token parse",
              f"(ts={r2[16:26]}, node 实跑捕获)")

    # 4. 请求 body 加密 + 解密 roundtrip
    got = get_request_data(AES_KEY, ORIGINAL_DATA)
    check(got == REQUEST_DATA, "request data AES", f"({len(got)} b64 chars)")
    dec = it(got, AES_KEY)
    check(dec == ORIGINAL_DATA, "request data decrypt roundtrip",
          f"({dec})")

    # 5. 真实响应解密 (2024-07-17 密文, samples.json)
    import pathlib
    samples = json.loads(
        (pathlib.Path(__file__).parent / "samples.json").read_text(encoding="utf-8"))
    plain = it(samples["cipher_b64"], AES_KEY)
    plain_sha = hashlib.sha256(json.dumps(plain, ensure_ascii=False,
                                          separators=(",", ":")).encode()).hexdigest()
    check(plain_sha == samples["plain_sha256"], "response decrypt sha256",
          f"({plain_sha[:16]}...)")
    f = samples["fields"]
    pos = plain["content"]["positionResult"]["result"][0]
    ok = (plain["success"] is True and plain["code"] == 0
          and plain["content"]["positionResult"]["totalCount"] == f["totalCount"]
          and pos["positionName"] == f["first_positionName"]
          and pos["companyFullName"] == f["first_company"]
          and pos["salary"] == f["first_salary"])
    check(ok, "response decrypt fields",
          f"(首条: {pos['positionName']} @ {pos['companyFullName']}, "
          f"{pos['salary']}, total={plain['content']['positionResult']['totalCount']})")

    # 6. AES roundtrip ×3 (固定 key, 不同明文; it() 可自动解析 JSON)
    for i, p in enumerate(["{\"a\":1}", ORIGINAL_DATA,
                           "{\"pn\":9,\"kd\":\"数据分析\"}"]):
        if not isinstance(p, str):
            p = json.dumps(p, ensure_ascii=False, separators=(",", ":"))
        dec = it(rt(p, AES_KEY), AES_KEY)
        dec_s = (json.dumps(dec, ensure_ascii=False, separators=(",", ":"))
                 if isinstance(dec, dict) else dec)
        check(dec_s == p, f"AES roundtrip #{i}", f"({p[:30]}...)")

    # 7. RSA 结构: 公钥 2048-bit/e=65537; 加密 32 字符 key -> 344 b64 / 256B
    #    (PKCS1v1.5 的 0x00 0x02 是填充消息的属性, 密文首位随机 —
    #     node 端 JSEncrypt 同输入输出 256B, 首位 50 37, 与 Python 行为一致)
    pub = RSA.import_key(RSA_PUB)
    check(pub.size_in_bits() == 2048 and pub.e == 65537,
          "RSA key params", "(2048-bit, e=65537)")
    rsa = rsa_encrypt_aes_key(AES_KEY)
    raw = base64.b64decode(rsa)
    check(len(rsa) == 344 and len(raw) == 256,
          "RSA encrypt structure",
          f"({len(rsa)} b64 -> {len(raw)}B, node 同: 344/256)")

    # 8. getAesKeyAndRsaEncryptData 全链模拟: key 字符集/长度 + RSA 结构
    k = gen_aes_key()
    check(len(k) == 32 and set(k) <= set(KEY_ALPHABET),
          "aes key alphabet", f"(len {len(k)}, {len(set(k))} distinct)")
    rsa = rsa_encrypt_aes_key(k)
    raw = base64.b64decode(rsa)
    check(len(rsa) == 344 and len(raw) == 256,
          "rsa(aesKey) structure", f"({len(rsa)} b64 chars)")
    # 同一明文两次 RSA 加密密文不同 (PKCS1v1.5 随机填充)
    check(rsa != rsa_encrypt_aes_key(k), "RSA random padding",
          "(两次密文不同)")

    # 9. traceparent 结构: "00-" + 32hex + "-" + 16hex + "-01"
    ok = True
    for _ in range(2):
        t = get_traceparent()
        ok = ok and bool(re.fullmatch(r"00-[0-9a-f]{32}-[0-9a-f]{16}-01", t))
    check(ok, "traceparent structure", f"({get_traceparent()})")

    print(f"\n{passed}/{total} passed")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
