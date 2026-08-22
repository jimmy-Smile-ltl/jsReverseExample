"""
一嗨租车 (booking.1hai.cn) — 双向 AES-256-CFB 加密通道

用法:
    python main.py            # 运行全部样例验证 (无需网络)

原理 (webpack module 2780, CryptoJS):
    Axios 拦截器 (module 4211) 对所有 API 做全量加解密:
        1. query 串  = operatorId&platform&platformSource&timestamp&原始参数 (qs.stringify)
           body 串   = JSON.stringify(body)
        2. encrypt:  AES-256-CFB (segment 128bit) + PKCS7 填充 (CryptoJS 显式指定,
           CFB 本不需要填充) -> 标准 Base64 -> '+'→'$', '='→'*' -> encodeURIComponent
        3. URL  = /bookingApiService/{path}?{加密query},  POST body = 加密body
        4. 响应同样加密, decrypt 后 JSON.parse
    密钥/IV 硬编码在 module 2780 ("testing" 环境, 即生产), AES-CFB 固定 IV
    无随机性 -> 相同明文恒得相同密文, 抓包密文可直接作为期望值。

样例来源: 2026-06-30 浏览器抓包 (逆向/逆向分析报告.md 8.2 节 + test.py)
"""

import base64
import json
import urllib.parse
from datetime import datetime

from Crypto.Cipher import AES  # pip install pycryptodome
from Crypto.Util.Padding import pad, unpad

# 密钥 (Base64 32 字节 -> AES-256) 与 IV (16 字节), 自 module 2780 提取
AES_KEY = base64.b64decode("R99N6Jr7ZuPN6KKr2UsnwLVMCEU7nGPwzBARo0cIfhg=")
AES_IV = base64.b64decode("LcP31iA3MVkRdDPn4/+3Dg==")

PLATFORM = 1010902
API_BASE = "/bookingApiService"


def js_b64_encode(data: bytes) -> str:
    """标准 Base64 后替换: '+'→'$', '='→'*' (JS 端 replace)"""
    return base64.b64encode(data).decode("ascii").replace("+", "$").replace("=", "*")


def js_b64_decode(s: str) -> bytes:
    """还原: '*'→'=', '$'→'+', 补 padding 后解码"""
    s = s.replace("$", "+").replace("*", "=")
    s += "=" * (4 - len(s) % 4)
    return base64.b64decode(s)


def encrypt(plaintext: str) -> str:
    """AES-CFB + PKCS7 -> 自定义 Base64 -> encodeURIComponent

    对应 JS: et.AES.encrypt(e, eo, {iv: ea, mode: CFB, padding: Pkcs7}).toString()
    注意 CryptoJS 的 CFB 显式带 Pkcs7 填充, pycryptodome 的 CFB 不自动填充,
    需手动 pad 后再加密 (segment_size=128 与 CryptoJS 默认一致)。
    """
    padded = pad(plaintext.encode("utf-8"), AES.block_size)
    cipher = AES.new(AES_KEY, AES.MODE_CFB, iv=AES_IV, segment_size=128)
    return urllib.parse.quote(js_b64_encode(cipher.encrypt(padded)), safe="")


def decrypt(ciphertext: str) -> str:
    """decodeURIComponent -> 自定义 Base64 还原 -> AES-CFB 解密 -> 去填充"""
    s = urllib.parse.unquote(ciphertext)
    if not s or not s.strip():
        return ""
    cipher = AES.new(AES_KEY, AES.MODE_CFB, iv=AES_IV, segment_size=128)
    padded = cipher.decrypt(js_b64_decode(s))
    return unpad(padded, AES.block_size).decode("utf-8")


def encrypt_aes(query: str, body: str = "") -> dict:
    """query 与 body 分别加密 (对应 JS encryptAES)"""
    result = {"query": "", "data": ""}
    if query:
        result["query"] = encrypt(query)
    if body:
        result["data"] = encrypt(body)
    return result


def build_encrypted_request(path: str, query_params: dict = None,
                            body_params: dict = None, operator_id: str = "",
                            platform_source: str = "") -> dict:
    """构建完整加密请求 (对应 JS 拦截器 B 函数)

    返回 {url, data, headers} + 明文参考字段; 时间戳格式 YYYY/MM/DD HH:mm:ss
    """
    merged = {
        "operatorId": operator_id,
        "platform": str(PLATFORM),
        "platformSource": platform_source,
        "timestamp": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
    }
    if query_params:
        merged.update(query_params)
    query_str = urllib.parse.urlencode(merged)
    body_str = json.dumps(body_params, separators=(",", ":")) if body_params else ""

    enc = encrypt_aes(query_str, body_str)
    return {
        "url": f"{API_BASE}{path}?{enc['query']}",
        "data": enc["data"],
        "headers": {"Content-Type": "application/json", "x-ehi-source-plat": "booking"},
        "_query_raw": query_str,
        "_body_raw": body_str,
    }


# ============================================================ 样例验证

# 真实抓包加密响应 -> 期望明文 (2026-06-30, 逆向分析报告 8.2 节)
CAPTURED = [
    ("pRi8dVUhrlpt0IPioUt2EKiMcaVt3ukOuOy0$3JbkRAi5SWhM2kyQarHmh/gPOOIPvpMDX1ulsZjDu22YW4SsCNW$t2vyOjX//DY6uIVLkGRMziVkaEydISE7NCxkTkB",
     '{"isSuccess":true,"errorCode":0,"operationId":"88a6a05fe5212a8a2fb491c67b2e5fff"}'),   # POST /Verify/Step1
    ("pRinY3UhoU0qmYSy7looRzPN$x9Pc7gXVMhyNBiij1cuF$4GLgdHECar9VKxA4Bkr0wt9q0RkAvKb1Qc0ckZsr72c4vGdYV$eq4qFd7h6eKsa49S5vHKYQuafnN4S7Xl",
     '{"result":true,"isSuccess":true,"errorCode":0,"operationId":"608335c80e78a329ca81f051ea686b9d"}'),  # POST /Address/IsAllowExempt
    ("pRinY3UhoU0qmdLyfputR8GiZ9Vk0m97dMCiHrEQtgFS7xUpIpLwvCC5IfGUFTFHNeh6EGj3vMl5wfZZJV4oG6sVGd4Lh6MiAmjL41AmZ9JEfK7540epGymmtvWSSg2lsZk8LRUqqK$3HoIt2vheJw**",
     '{"result":"2天","isSuccess":true,"errorCode":0,"operationId":"0893f56651489b9bcda99aa327daad00"}'),  # GET /Order/Format/RentDay -> result "2天"
]


def main() -> None:
    passed = 0
    total = 0

    def check(ok: bool, label: str, detail: str = "") -> None:
        nonlocal passed, total
        total += 1
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label} {detail}")

    # 1. 真实抓包密文 -> 明文 (AES-CFB 固定 IV 无随机性, 密文恒等)
    for i, (cipher, expect) in enumerate(CAPTURED):
        got = decrypt(cipher)
        check(got == expect, f"captured decrypt #{i}", f"(len {len(cipher)} -> {len(got)})")

    # 2. 加密确定性: 相同明文两次加密恒等 (固定 key/IV, 无随机分量)
    q = "operatorId=123&platform=1010902&timestamp=2026/06/30 12:00:00"
    check(encrypt(q) == encrypt(q), "encrypt deterministic", "(same input -> same ciphertext)")

    # 3. 加密 -> 解密往返 (query / json / 中文+特殊字符 三种形态)
    roundtrips = [
        "operatorId=123&platform=1010902&platformSource=&timestamp=2026/06/30 12:00:00",
        '{"storeId":123,"cityName":"上海"}',                    # {"storeId":123,"cityName":"上海"}
        "中文测试 !@#$%^&*()_+-=[]{}|;':\",./<>?",       # 中文测试 + 特殊字符
    ]
    for i, text in enumerate(roundtrips):
        enc = encrypt(text)
        check(decrypt(enc) == text, f"roundtrip #{i}", f"(len {len(text)} -> {len(enc)})")

    # 4. 完整请求结构: URL 前缀 + body 密文可解密 + headers
    req = build_encrypted_request(
        "/Verify/Step1",
        query_params={"carId": "ABC123", "cityCode": "310000"},
        body_params={"storeId": 123, "cityName": "上海"},
        operator_id="op01",
    )
    q_dec = decrypt(req["url"].split("?", 1)[1])
    b_dec = decrypt(req["data"])
    check(req["url"].startswith(f"{API_BASE}/Verify/Step1?") and q_dec == req["_query_raw"]
          and b_dec == req["_body_raw"] and req["headers"]["x-ehi-source-plat"] == "booking",
          "request builder", f"(url len {len(req['url'])}, body len {len(req['data'])})")

    print(f"\n{passed}/{total} passed")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
