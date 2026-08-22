"""
网易云音乐 (music.163.com) — weapi 参数加密 (双层 AES-128-CBC + RSA-1024)

用法:
    python main.py            # 运行全部样例验证 (无需网络)

原理 (core.js window.asrsea):
    1. 生成 16 位随机密钥 (a-zA-Z0-9)
    2. 明文 JSON -> AES-128-CBC 固定密钥 "0CoJUm6Qyw8W8jud" (固定 IV "0102030405060708") -> base64
    3. 上一步结果再用随机密钥做第二次 AES-128-CBC -> base64 = params
    4. 随机密钥 RSA-1024 加密 -> hex = encSecKey
    POST /weapi/...?csrf_token=XXX  body = params=...&encSecKey=...

JS -> Python 关键差异:
    - CryptoJS 传字符串会走 KDF 派生密钥, 必须 Utf8.parse 显式转 WordArray -> Python 直接 .encode()
    - JS RSA 是零填充 (非 PKCS#1 v1.5): 明文补 \\x00 到 126 字节, BigInt digit 按
      little-endian 16-bit 字 -> Python: int.from_bytes(padded, 'little'), pow 后 hex
    - json.dumps 必须 separators=(',', ':') + ensure_ascii=False 对齐 JS JSON.stringify

样例来源: 期望值 2026-06-30 浏览器验证 (ANALYSIS_REPORT 6.2); 真实抓包 2026-06-30
"""

import base64
import json
import random
import urllib.parse

from Crypto.Cipher import AES  # pip install pycryptodome
from Crypto.Util.Padding import pad, unpad

FIXED_AES_KEY = "0CoJUm6Qyw8W8jud"   # 固定 AES 密钥 (16 字节 = AES-128)
AES_IV = b"0102030405060708"         # 固定 IV
RSA_EXPONENT = 0x010001              # 65537
RSA_MODULUS = int(
    "00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725"
    "152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312"
    "ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424"
    "d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7", 16)
RSA_CHUNK_SIZE = 126                 # 1024-bit RSA chunk (剩余 2 字节留给前导进位)
RANDOM_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def generate_random_key(length: int = 16) -> str:
    """随机 16 位密钥 (对应 JS 函数 a)"""
    return "".join(random.choice(RANDOM_CHARS) for _ in range(length))


def aes_encrypt_base64(plaintext: str, key: str) -> str:
    """AES-128-CBC + PKCS7 -> base64 (对应 JS 函数 b)"""
    cipher = AES.new(key.encode("utf-8"), AES.MODE_CBC, AES_IV)
    return base64.b64encode(cipher.encrypt(pad(plaintext.encode("utf-8"),
                                               AES.block_size))).decode()


def aes_decrypt_base64(ciphertext: str, key: str) -> str:
    """逆向: base64 -> AES-128-CBC 解密 (验证用)"""
    cipher = AES.new(key.encode("utf-8"), AES.MODE_CBC, AES_IV)
    return unpad(cipher.decrypt(base64.b64decode(ciphertext)), AES.block_size).decode("utf-8")


def rsa_encrypt(text: str) -> str:
    """RSA-1024 零填充小端加密 -> hex (对应 JS encryptedString + RSAKeyPair)

    明文补 \\x00 到 126 字节; JS BigInt digit 为 little-endian 16-bit 字,
    Python 等价写法 int.from_bytes(padded, 'little'); 密文 hex 不定长 (不补前导零)。
    """
    padded = text.encode("utf-8") + b"\x00" * (RSA_CHUNK_SIZE - len(text))
    msg_int = int.from_bytes(padded, "little")
    return format(pow(msg_int, RSA_EXPONENT, RSA_MODULUS), "x")


def encrypt_request(data: dict, random_key: str = None) -> dict:
    """主加密 (对应 window.asrsea): 返回 {"params", "encSecKey"}"""
    plaintext = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    if random_key is None:
        random_key = generate_random_key(16)
    first_pass = aes_encrypt_base64(plaintext, FIXED_AES_KEY)
    params = aes_encrypt_base64(first_pass, random_key)
    return {"params": params, "encSecKey": rsa_encrypt(random_key)}


def encrypt_request_urlencoded(data: dict) -> str:
    """返回可直接 POST 的 body: params=...&encSecKey=..."""
    enc = encrypt_request(data)
    return ("params=" + urllib.parse.quote(enc["params"]) +
            "&encSecKey=" + urllib.parse.quote(enc["encSecKey"]))


# ============================================================ 样例验证

# 1. 浏览器验证期望值 (2026-06-30): 固定明文 + 固定随机密钥, 逐层比对
FIXED_PLAINTEXT = json.dumps({"ids": "[123]", "level": "standard", "encodeType": "aac"},
                             separators=(",", ":"))
FIXED_RANDOM_KEY = "aaaaaaaaaaaaaaaa"
EXPECT_FIRST = "++C8Kduj9nwY38mnyfn0wIM/vjH83gEUYCwSd5eBnAYFEmbFyO5+motDTvXsoMG0LxrVNjg9R+D/LEp/FDEIKg=="
EXPECT_SECOND = "zij5f2KUEeTWDEyl6EUd1N0vCi790dsXM/z/I8LySLTUKAJrYPs9i8qrxP8T3nNQ3wJIkqghXhV4CFTIwGaV5+sRgJrsR3AclerH3Zxaz9L0F2CgJjNcaMBw4OiwmzXH"
EXPECT_RSA = "d473b9eca232f1b4090dd606b0df86de318748dd2eec307e4ed4345030fc4ee30331e598f41d5a6f5befaab94630ea1a1eda7cfade84fbec1a907913d2e4d2c8744bc572b99a050075e075b4537f645ecfa994f95906c32818e076aeda6bdb906bfa0bb96c4cf4bc3ed6d9ab76cf08441153d9d85e1ea3d78fa8d9210d581cee"

# 2. 真实抓包请求 (2026-06-30, POST /weapi/song/enhance/player/url/v1)
CAPTURED_PARAMS = ("rKIHI45hCawMLDKYHim26s9plSimrabKGWMkG8lNzsJtShPRa2PGMZTilymA2cyPWzEa2AwATlxdoDHI%2F%2B7PPCn%2FFrFM%2BvCwMKcdrP6svMVmJwDIb0sqOQmRKL517GstyHG0XanMUinn4DXDTbnlgbxW2Mqs5cpOY8DYX7Zpy8Bkml71aFHYBYrDFGKnqhlwHyldZrelGnjx1mbuVdkPeg%3D%3D")
CAPTURED_SECKEY = "0dbc3673eb24cbda44129f3a38b350380cecec64f5f45098f1e9f715f28cc7b72c8f185ddf040db92023f8d5375c9029bfb618c7985af6691f8ec159ff1df3edfe0b93063d6af155394d4c6932cd3863761b3471dca94ac6ee2e7fbffd28508e8e948cf47c3f836db6089138e964d322fa0a1fca6b1fb5bc411c2c339288d01a"


def main() -> None:
    passed = 0
    total = 0

    def check(ok: bool, label: str, detail: str = "") -> None:
        nonlocal passed, total
        total += 1
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label} {detail}")

    # 1. 浏览器验证期望值: 第一次 AES / 第二次 AES / RSA 逐层比对
    got_first = aes_encrypt_base64(FIXED_PLAINTEXT, FIXED_AES_KEY)
    got_second = aes_encrypt_base64(got_first, FIXED_RANDOM_KEY)
    got_rsa = rsa_encrypt(FIXED_RANDOM_KEY)
    check(got_first == EXPECT_FIRST, "AES layer 1 vs browser", f"(len {len(got_first)})")
    check(got_second == EXPECT_SECOND, "AES layer 2 vs browser", f"(len {len(got_second)})")
    check(got_rsa == EXPECT_RSA, "RSA vs browser", f"(len {len(got_rsa)})")

    # 2. 完整加密往返: 含中文 + 嵌套字段, 用同一随机密钥解密还原
    data = {"ids": "[2755014796]", "level": "standard", "encodeType": "aac",
            "keywords": "周杰伦 晴天", "limit": 30, "offset": 0}
    key = "BCdef1234567890X"
    enc = encrypt_request(data, random_key=key)
    inner = aes_decrypt_base64(enc["params"], key)
    restored = json.loads(aes_decrypt_base64(inner, FIXED_AES_KEY))
    check(restored == data, "full flow roundtrip", "(with Chinese, nested)")

    # 3. URL 编码 body 格式
    body = encrypt_request_urlencoded({"ids": "[123]", "level": "standard", "encodeType": "aac"})
    check(body.startswith("params=") and "&encSecKey=" in body, "urlencoded body",
          f"(len {len(body)})")

    # 4. 真实抓包请求结构: params 为合法 base64 且 CBC 块对齐 (16 字节倍数)
    params_raw = urllib.parse.unquote(CAPTURED_PARAMS)
    ok = (len(params_raw) % 4 == 0 and len(base64.b64decode(params_raw)) % 16 == 0)
    check(ok, "captured params structure", f"(b64 len {len(params_raw)})")
    # encSecKey 恒为 256 hex 字符 (128 字节 = 1024-bit RSA 输出)
    check(len(CAPTURED_SECKEY) == 256 and all(c in "0123456789abcdef" for c in CAPTURED_SECKEY),
          "captured encSecKey structure", f"(hex len {len(CAPTURED_SECKEY)})")

    print(f"\n{passed}/{total} passed")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
