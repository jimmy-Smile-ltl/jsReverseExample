"""
内蒙古农机购置补贴 (111.56.142.13:18088/subsidyOpen) — 国密 SM4-ECB + SM3 + RSA-512 密钥护送

用法:
    python main.py            # 运行全部样例验证 (无需网络)

原理:
    请求头三件套 (每个字段均为 SM4-ECB 密文 hex):
        sign      = SM4( SM3( 排序查询串 + "&key=" + API_KEY ).upper() )
        timestamp = SM4( str(毫秒时间戳) )
        parameter = SM4( JSON(请求体) )    (POST body: {"parameter": 密文})
    SM4 key 固定: RSA-512 PKCS#1 v1.5 私钥解密 ENCRYPTED_SM4_KEY (返回 32 字符 hex 串,
                  再 bytes.fromhex 得 16 字节 key) —— 一次性引导, 运行时直接复用
    source 固定: ZRCSL7V0JIRK1PHY

JS -> Python 关键差异:
    - 签名查询串: key 按字母排序, 过滤空值 (None/\"\"/0), encodeURIComponent(key)=value
    - RSA 私钥固定硬编码在客户端 (PKCS#8 DER), 本复现提取 n/d 纯 Python 解密,
      不依赖 cryptography 库
"""

import base64
import json
import time

from gmssl.sm3 import sm3_hash          # pip install gmssl
from gmssl.sm4 import CryptSM4, SM4_ENCRYPT, SM4_DECRYPT

API_KEY = "HD7232D2AAAKA@978D8723H211?IER&6"
SOURCE = "ZRCSL7V0JIRK1PHY"
BASE_URL = "http://111.56.142.13:18088"

# RSA-512 私钥参数 (PKCS#8 DER 提取, 硬编码于客户端 JS)
RSA_N = 0xd2f7efc9374626475b1e407c9a9d1fdc51341983f70183da245ee351dd4cd17c45484d9c78ade4da4c36d18bd0d3d3492a4f8e32359097d5a2b46f6907ab5209
RSA_D = 0x364a2981ad60b6ff0bdab81b98aa3085c0bbd889162a64a4e1512dcc66579b5c988b07e51efe05227c000a220d5abedb5466c1c11eba29e2a7c90b0008d3e611
RSA_ENCRYPTED_KEY_B64 = "e3xFjZ4ezDBUbyMbdwwTH+GzxbOe7kHsn4YNMr1j4KerhffMsEXu5GEVad4hpIj2XRQkBRAfKFhk1u5IlLdKLw=="

EXPECTED_SM4_KEY_HEX = "30062AFC48C0E7B5B0918851C0445A37"  # RSA 解出的 32 字符 hex 串


def rsa_pkcs1v15_decrypt(ciphertext_b64: str) -> bytes:
    """RSA-512 PKCS#1 v1.5 解密 (m = c^d mod n, 剥 00 02 PS 00)"""
    c = int.from_bytes(base64.b64decode(ciphertext_b64), "big")
    m = pow(c, RSA_D, RSA_N)
    raw = m.to_bytes(64, "big")          # 512-bit -> 64 字节
    assert raw[0] == 0 and raw[1] == 2    # PKCS#1 v1.5 头
    sep = raw.index(0, 2)                 # 00 02 <PS> 00 <data>
    return raw[sep + 1:]


def get_sm4_key() -> bytes:
    """一次性引导: RSA 解密 -> 32 字符 hex 串 -> bytes.fromhex 得 16 字节 SM4 key"""
    sm4_key_hex = rsa_pkcs1v15_decrypt(RSA_ENCRYPTED_KEY_B64).decode("utf-8")
    return bytes.fromhex(sm4_key_hex)


SM4_KEY = get_sm4_key()


def sm4_encrypt(plaintext: str) -> str:
    """SM4-ECB (PKCS7 填充) -> hex 密文"""
    cipher = CryptSM4()
    cipher.set_key(SM4_KEY, SM4_ENCRYPT)
    return cipher.crypt_ecb(plaintext.encode("utf-8")).hex()


def sm4_decrypt(ciphertext_hex: str) -> str:
    """hex 密文 -> SM4-ECB 解密"""
    cipher = CryptSM4()
    cipher.set_key(SM4_KEY, SM4_DECRYPT)
    return cipher.crypt_ecb(bytes.fromhex(ciphertext_hex)).decode("utf-8")


def sm3_hex(text: str) -> str:
    """SM3 哈希 (gmssl 接口要求 list[int])"""
    return sm3_hash(list(text.encode("utf-8")))


def build_sign_query(data: dict) -> str:
    """签名查询串: key 排序 + 过滤空值 + encodeURIComponent(key)=value"""
    parts = []
    for key in sorted(data.keys()):
        val = data[key]
        if val is None or val == "" or val == 0:
            continue
        if isinstance(val, (dict, list)):
            val_str = json.dumps(val, separators=(",", ":"), ensure_ascii=False)
        else:
            val_str = str(val)
        parts.append(f"{key}={val_str}")
    return "&".join(parts)


def generate_sign(data: dict, timestamp_ms: int) -> str:
    """sign = SM4( SM3(查询串 + &key=API_KEY).upper() )"""
    query = build_sign_query({**data, "timestamp": timestamp_ms})
    return sm4_encrypt(sm3_hex(query + "&key=" + API_KEY).upper())


def generate_timestamp(timestamp_ms: int) -> str:
    """timestamp = SM4(str(毫秒))"""
    return sm4_encrypt(str(timestamp_ms))


def encrypt_parameter(params: dict) -> str:
    """parameter = SM4(JSON)"""
    return sm4_encrypt(json.dumps(params, separators=(",", ":"), ensure_ascii=False))


def build_headers(data: dict, timestamp_ms: int) -> dict:
    """完整请求头 (sign/timestamp/source/urlprefix 四件套)"""
    return {
        "sign": generate_sign(data, timestamp_ms),
        "timestamp": generate_timestamp(timestamp_ms),
        "source": SOURCE,
        "urlprefix": "",
        "Content-Type": "application/json;charset=UTF-8",
    }


# ============================================================ 样例验证

def main() -> None:
    passed = 0
    total = 0

    def check(ok: bool, label: str, detail: str = "") -> None:
        nonlocal passed, total
        total += 1
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label} {detail}")

    # 1. RSA-512 PKCS#1 v1.5 引导: 解密得到 SM4 key (32 字符 hex 串)
    key_hex = rsa_pkcs1v15_decrypt(RSA_ENCRYPTED_KEY_B64).decode("utf-8")
    check(key_hex == EXPECTED_SM4_KEY_HEX, "RSA bootstrap -> SM4 key hex", f"({key_hex})")

    # 2. SM4-ECB 往返 (中文 JSON / 特殊字符)
    for i, text in enumerate([
        '{"year":2026,"pageNum":1,"pageSize":5,"applyType":1}',
        '购机者姓名-张三-农机购置补贴 @#$%^&*',
    ]):
        check(sm4_decrypt(sm4_encrypt(text)) == text, f"SM4 roundtrip #{i}", f"(len {len(text)})")

    # 3. sign 自洽: 解密 sign -> 重算 SM3 期望值一致 + 确定性
    data = {"year": 2026, "pageNum": 1, "pageSize": 5, "applyType": 1,
            "buyerName": "", "code": "", "status": "已公示"}
    ts = 1754123456789
    sign = generate_sign(data, ts)
    signed_raw = data | {"timestamp": ts}
    expect = sm3_hex(build_sign_query(signed_raw) + "&key=" + API_KEY).upper()
    check(sm4_decrypt(sign) == expect, "sign self-consistent",
          f"(sm4 len {len(sign)}, expect {expect[:24]}...)")
    check(sign == generate_sign(data, ts), "sign deterministic", f"(hex len {len(sign)})")

    # 4. timestamp 可还原 + 确定性
    ts_enc = generate_timestamp(ts)
    check(sm4_decrypt(ts_enc) == str(ts), "timestamp roundtrip", f"(hex len {len(ts_enc)})")

    # 5. parameter 可还原 (中文 JSON)
    param_enc = encrypt_parameter(data)
    check(json.loads(sm4_decrypt(param_enc)) == data, "parameter roundtrip",
          f"(hex len {len(param_enc)})")

    # 6. 完整请求结构: headers 四件套 + body
    headers = build_headers(data, ts)
    body = {"parameter": encrypt_parameter(data)}
    ok = (set(headers) >= {"sign", "timestamp", "source", "urlprefix"})
    check(ok and headers["source"] == SOURCE and headers["urlprefix"] == ""
          and set(body) == {"parameter"} and body["parameter"] == param_enc,
          "request structure", f"(sign {len(headers['sign'])}, ts {len(headers['timestamp'])})")

    print(f"\n{passed}/{total} passed")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
