"""
中国空气质量在线监测分析平台 (aqistudy.cn) — 混淆 + 双重加密

用法:
    python main.py            # 运行全部样例验证 (无需网络)

原理:
    API: POST /apinew/aqistudyapi.php, 参数名固定 h1zlb1QoZ
    请求加密: JSON(含 secret) -> Base64  (2026.06 升级后仅一层 Base64, 旧版有 AES 层)
        secret = MD5(appId + method + timestamp + clienttype + JSON(sorted(obj)))
    响应解密: Base64 -> AES-CBC -> Base64 -> DES-CBC -> Base64 -> JSON
        密钥派生(坑): MD5(原始密钥) 的 hex 串按 UTF-8 字节使用, 不是 hex 解码!
        AES key = MD5(a5slhqEdLos7hvjr)[16:32] (16 hex chars -> 16 utf8 bytes)
        AES iv  = MD5(bhb9eTODiif32jv0)[0:16]
        DES key = MD5(hXenRdbrF1iqaMLr)[0:16] 取前 8 字节 (单 DES)
        DES iv  = MD5(xAWozmps3eqYftMA)[24:32] (8 hex chars -> 8 utf8 bytes)
    函数名混淆: pvkWB5TRrM9kT5 (请求加密) / d6o2KJrVnYKBvdlc6mTrx4 (响应解密)

样例说明: 实战响应密文未留存 (2026-06-29 实测北京/上海/广州请求成功, 见 README);
         验证用密钥派生确定性 + 构造解密链自洽 + 请求加密确定性。
"""

import base64
import hashlib
import json
import time

from Crypto.Cipher import AES, DES  # pip install pycryptodome
from Crypto.Util.Padding import pad, unpad

# 密钥常量 (自 JS 提取)
AES_KEY_RAW = "a5slhqEdLos7hvjr"
AES_IV_RAW = "bhb9eTODiif32jv0"
DES_KEY_RAW = "hXenRdbrF1iqaMLr"
DES_IV_RAW = "xAWozmps3eqYftMA"
APP_ID = "0e5df784c9068129938846e4fd750fdd"
CLIENT_TYPE = "WEB"


def derive_aes_key_iv() -> tuple[str, str]:
    """AES key = MD5(KEY_RAW) hex 的 [16:32], iv = MD5(IV_RAW) hex 的 [0:16]"""
    key_md5 = hashlib.md5(AES_KEY_RAW.encode()).hexdigest()
    iv_md5 = hashlib.md5(AES_IV_RAW.encode()).hexdigest()
    return key_md5[16:32], iv_md5[0:16]


def derive_des_key_iv() -> tuple[str, str]:
    """DES key = MD5(KEY_RAW) hex 的 [0:16] 取前 8 字节, iv = MD5(IV_RAW) hex 的 [24:32]"""
    key_md5 = hashlib.md5(DES_KEY_RAW.encode()).hexdigest()
    iv_md5 = hashlib.md5(DES_IV_RAW.encode()).hexdigest()
    return key_md5[0:16], iv_md5[24:32]


def decrypt_response(encrypted_text: str) -> dict:
    """响应解密链: Base64 -> AES-CBC -> Base64 -> DES-CBC -> Base64 -> JSON"""
    aes_key_str, aes_iv_str = derive_aes_key_iv()
    des_key_str, des_iv_str = derive_des_key_iv()

    aes_ct = base64.b64decode(encrypted_text)
    plain_aes = unpad(AES.new(aes_key_str.encode(), AES.MODE_CBC,
                              aes_iv_str.encode()).decrypt(aes_ct), AES.block_size)
    des_b64 = plain_aes.decode("utf-8")

    des_ct = base64.b64decode(des_b64)
    plain_des = unpad(DES.new(des_key_str.encode()[:8], AES.MODE_CBC,
                              des_iv_str.encode()).decrypt(des_ct), DES.block_size)
    inner_b64 = plain_des.decode("utf-8")

    return json.loads(base64.b64decode(inner_b64).decode("utf-8"))


def encrypt_response(data: dict) -> str:
    """反向构造解密链 (JSON -> Base64 -> DES-CBC -> Base64 -> AES-CBC -> Base64), 用于自洽验证"""
    aes_key_str, aes_iv_str = derive_aes_key_iv()
    des_key_str, des_iv_str = derive_des_key_iv()

    inner_b64 = base64.b64encode(json.dumps(data, ensure_ascii=False).encode()).decode()
    des_ct = DES.new(des_key_str.encode()[:8], AES.MODE_CBC,
                     des_iv_str.encode()).encrypt(pad(inner_b64.encode(), DES.block_size))
    des_b64 = base64.b64encode(des_ct).decode()
    aes_ct = AES.new(aes_key_str.encode(), AES.MODE_CBC,
                     aes_iv_str.encode()).encrypt(pad(des_b64.encode(), AES.block_size))
    return base64.b64encode(aes_ct).decode()


def encrypt_request(method: str, obj: dict, timestamp: int = None) -> str:
    """请求加密: 排序 keys -> secret=MD5(appId+method+ts+clienttype+json) -> Base64"""
    if timestamp is None:
        timestamp = int(time.time() * 1000)
    sorted_obj = json.dumps(dict(sorted(obj.items())), ensure_ascii=False, separators=(",", ":"))
    secret_raw = APP_ID + method + str(timestamp) + CLIENT_TYPE + sorted_obj
    secret = hashlib.md5(secret_raw.encode()).hexdigest()
    param = {"appId": APP_ID, "method": method, "timestamp": timestamp,
             "clienttype": CLIENT_TYPE, "object": obj, "secret": secret}
    return base64.b64encode(json.dumps(param, ensure_ascii=False,
                                       separators=(",", ":")).encode()).decode()


# ============================================================ 样例验证

def main() -> None:
    passed = 0
    total = 0

    def check(ok: bool, label: str, detail: str = "") -> None:
        nonlocal passed, total
        total += 1
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label} {detail}")

    # 1. 密钥派生确定性 (期望值内嵌, 自 JS 计算流程)
    aes_k, aes_i = derive_aes_key_iv()
    des_k, des_i = derive_des_key_iv()
    check(aes_k == "3d46d26fc8ce74ce", "derive AES key", f"-> {aes_k}")
    check(aes_i == "34ee4a6f79804a33", "derive AES iv ", f"-> {aes_i}")
    check(des_k == "2a754300e6b936f0", "derive DES key", f"-> {des_k}")
    check(des_i == "83c31b56", "derive DES iv ", f"-> {des_i}")

    # 2. 解密链自洽: 构造 -> 解密还原 (真实数据结构)
    payloads = [
        {"success": True, "result": {"success": True, "data": {"rows": [{"time": "2026-06-29 09:00:00", "aqi": 42, "pm2_5": 15}]}}},
        {"success": True, "result": {"success": True, "data": {"rows": [{"time": "2026-06-29 10:00:00", "temp": 28, "humi": 62, "tq": "多云"}]}}},
        {"success": False, "errorCode": 101},
    ]
    for i, p in enumerate(payloads):
        enc = encrypt_response(p)
        check(decrypt_response(enc) == p, f"decrypt chain #{i}", f"(len {len(enc)})")

    # 3. 请求加密: 固定 timestamp -> 确定性输出 + secret 重算自洽
    for i, (method, obj) in enumerate([
        ("GETDETAIL", {"city": "北京", "type": "HOUR", "startTime": "2026-06-28 09:00:00", "endTime": "2026-06-29 12:00:00"}),
        ("GETCITYWEATHER", {"city": "上海", "type": "DAY", "startTime": "2026-06-01", "endTime": "2026-06-29"}),
    ]):
        ts = 1782700000000 + i
        enc1 = encrypt_request(method, obj, ts)
        enc2 = encrypt_request(method, obj, ts)
        ok = enc1 == enc2
        if ok:  # 重算 secret 自洽
            inner = json.loads(base64.b64decode(enc1).decode())
            sorted_obj = json.dumps(dict(sorted(obj.items())), ensure_ascii=False, separators=(",", ":"))
            expect = hashlib.md5((APP_ID + method + str(ts) + CLIENT_TYPE + sorted_obj).encode()).hexdigest()
            ok = inner["secret"] == expect
        check(ok, f"request encrypt #{i}", f"(base64 len {len(enc1)}, ts={ts})")

    # 4. 请求格式: h1zlb1QoZ 字段结构
    inner = json.loads(base64.b64decode(encrypt_request("GETDETAIL", {"city": "杭州", "type": "HOUR"}, 1782700001234)).decode())
    check(set(inner.keys()) == {"appId", "method", "timestamp", "clienttype", "object", "secret"},
          "request structure", f"(keys={sorted(inner)})")

    print(f"\n{passed}/{total} passed")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
