"""
中国观鸟记录中心 (birdreport.cn) — 请求签名 (RSA-1024 分块 + MD5) + 响应 AES-128-CBC 解密

用法:
    python main.py         # 签名链 + AES 解密 + RSA 结构 + 详情 URL (纯 Python, 无网络)
    python main.py --live  # 追加真实请求: RSA body + sign headers -> 服务端验签 -> AES 解密

原理 (before_ajax.js header_data(), 2024-12 原项目抓包, 2026-08 站点 jqueryAjax.js 比对一致):
    1. param(): 每 key/value encodeURIComponent 后 "k=v" 用 & 连接 (值保持 %XX 形态)
    2. dataTojson(): 按 & 与 = 切回 dict (值仍为 %XX 形态)
    3. sort_ASCII(): 按键名升序 (JS 默认字典序)
    4. JSON.stringify() 紧凑序列化 -> 明文 JSON
    5. body = RSA-1024/PKCS1v1.5 分块加密 (117 字符/块, hex 拼接后 base64)
    6. sign = MD5(明文JSON + requestId + timestamp)   <-- 明文参与 MD5, 不是密文!
    7. headers: sign / timestamp(字符串) / requestid; body 为 RSA 密文

    响应: data 字段 = AES-128-CBC (key C8EB5514AF5ADDB94B2207B08C66601C,
          iv 55DD79C6F04E1A67, Pkcs7) -> UTF-8 JSON 数组

样例来源: test.ipynb (2024-12-17 抓包/调试) + 2026-08-20 纯 Python 实测抓包三元组.
"""

import base64
import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request

# pycryptodome (pip install pycryptodome)
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.PublicKey import RSA

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

# 站点 RSA 公钥 (before_ajax.js paramPublicKey, DER 裸公钥)
PUBLIC_KEY = ("MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCvxXa98E1uWXnBzXkS2yHUfnBM6"
              "n3PCwLdfIox03T91joBvjtoDqiQ5x3tTOfpHs3LtiqMMEafls6b0YWtgB1dse1W5m+F"
              "peusVkCOkQxB4SZDH6tuerIknnmB/Hsq5wgEkIvO5Pff9biig6AyoAkdWpSek/1/B7"
              "zYIepYY0lxKQIDAQAB")
AES_KEY = "C8EB5514AF5ADDB94B2207B08C66601C"
AES_IV = "55DD79C6F04E1A67"

# 2026-08-20 真实抓包: 参与签名的明文 JSON / requestId / timestamp / sign (search 接口)
REAL_JSON = '{"endTime":"","limit":"50","page":"1","province":"%E5%9B%9B%E5%B7%9D","startTime":"","version":"CH4"}'
REAL_RID = "1e9ee1d9e9a3401e94124734939d41b8"
REAL_TS = 1787156945179
REAL_SIGN = "34988ec78cf446d96cf4ea0a5e2c120f"

# 2024-12-17 调试样例: 该次 encryptLong 返回 false, sign = MD5("false"+rid+ts)
DEBUG_RID = "1da2ab8e78cfe74fc379141787cabe63"
DEBUG_TS = 1734425821000
DEBUG_SIGN = "f786c300dffb34c3ea9cd89745486c9b"

# 2024-12-17 真实响应密文 (test.ipynb / 解码.js 内嵌) -> 期望 JSON 关键字段
AES_CIPHER = ("qBNIsXB+1H9ZTVg8FObe0ZK1pnkqapF4OYOuCdmvH7uey8YVbdwK/UhFaKa670qPA0UsOV"
              "wphP3wmu+XEySH94E9x/wfcok/kE2s6yiM48jrK8uWbjgdeO12FUAZGCeswqCd4mwvs7Ic+bag8"
              "N2U5ByDJopP975WJn/BBNdcunTWU698VZKcg9VBNIFBS1wKFNv+ssUvOGTibBOnQ0WaSLXVUl"
              "VBokS5j8GzMNtYr4iwmJ4gPSb8ClCcjFxocJxMXcbvNrM7lAXMUL7OeRV2gPuFRPBJUIu6HJo"
              "VVbdt9quyXfJtkd8rYL36x8/CSkNRxpJ2K4OJvQ348yLWIWkr9+cUYwCiqYXdUFSLFFwpTjzc"
              "b1tUmTShS2394HG/oZpqe8v+D+wvXAuKLKtmHUfmZnEIWn6it51JlnyOPu304LgDvLwbeLVol"
              "Xp0x2QgURoldVKK8g1L5x7cVvlCohSM7p7wFGaYXG9DLiyuYhCeyI4IYO2nmGm/7axMtMH975SA")
AES_EXPECT = {
    "address": "云南省保山市隆阳区蒲缥镇", "reportId": "e6d33531-4f82-479d-90b2-d8404ef2ef4b",
    "serialId": "2024010102309", "username": "ptarmigan", "state": 2,
}


def header_data(data: dict, request_id: str, timestamp_ms: int) -> tuple:
    """对应 before_ajax.js header_data(): 返回 (body_rsa_b64, sign, requestId, timestamp_str)

    param -> dataTojson -> sort_ASCII -> JSON.stringify -> RSA + MD5
    """
    def q(s):
        return urllib.parse.quote(str(s), safe="!~*'()")
    params = "&".join(f"{q(k)}={q(v)}" for k, v in data.items())
    pairs = []
    for item in params.split("&"):
        k, _, v = item.partition("=")
        pairs.append((k, v))
    json_str = json.dumps(dict(sorted(pairs)), separators=(",", ":"))
    body = rsa_encrypt_long(json_str)
    sign = hashlib.md5(f"{json_str}{request_id}{timestamp_ms}".encode()).hexdigest()
    return body, sign, request_id, str(timestamp_ms)


def rsa_encrypt_long(plain: str) -> str:
    """对应 RSAKey.encryptLong: 117 字符/块 + PKCS1v1.5 加密, hex 拼接后 base64"""
    pub = RSA.import_key(base64.b64decode(PUBLIC_KEY))
    max_block = (pub.size_in_bits() + 7 >> 3) - 11  # (1024+7>>3)-11 = 117
    chunks = [plain[i:i + max_block] for i in range(0, len(plain), max_block)]
    hexs = "".join(PKCS1_v1_5.new(pub).encrypt(c.encode()).hex() for c in chunks)
    return base64.b64encode(bytes.fromhex(hexs)).decode()


def data_decode(cipher_b64: str) -> dict:
    """对应 解码.js data_decode: AES-128-CBC + Pkcs7 -> UTF-8 JSON"""
    cipher = base64.b64decode(cipher_b64)
    plain = AES.new(AES_KEY.encode(), AES.MODE_CBC, AES_IV.encode()).decrypt(cipher)
    pad = plain[-1]
    plain = plain[:-pad]
    return json.loads(plain.decode("utf-8"))


def record_url(report_id: str, ts: int) -> str:
    """对应 detail.js getRecordUrl: param=Base64(JSON) + sign=calcMD5(对象) -> MD5("")"""
    param = base64.b64encode(
        json.dumps({"reportId": report_id, "ts": ts}, separators=(",", ":")).encode()).decode()
    sign = hashlib.md5(b"").hexdigest()  # calcMD5(对象) 返回 "" -> MD5 空串 (固定 sign)
    return f"https://www.birdreport.cn/home/record/page.html?param={param}&sign={sign}"


def main() -> None:
    passed, total = 0, 0

    def check(ok: bool, label: str, detail: str = "") -> None:
        nonlocal passed, total
        total += 1
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label} {detail}")

    # 1. 参数序列化链: 中文 -> %XX 形态, 键升序, 紧凑 JSON (期望 = 2026-08-20 真实抓包)
    data = {"page": 1, "limit": 50, "province": "四川", "startTime": "",
            "endTime": "", "version": "CH4"}
    def q(s):
        return urllib.parse.quote(str(s), safe="!~*'()")
    params = "&".join(f"{q(k)}={q(v)}" for k, v in data.items())
    pairs = [item.partition("=") for item in params.split("&")]
    json_str = json.dumps(dict(sorted((k, v) for k, _, v in pairs)), separators=(",", ":"))
    check(json_str == REAL_JSON, "param->sort->stringify chain",
          f"({json_str})")

    # 2. sign 计算: MD5(明文JSON + rid + ts) == 真实抓包 sign
    sign = hashlib.md5(f"{REAL_JSON}{REAL_RID}{REAL_TS}".encode()).hexdigest()
    check(sign == REAL_SIGN, "sign = MD5(plain json + rid + ts)",
          f"({sign})")

    # 3. sign 机制调试样例 (2024-12-17): RSA 失败时拼接 "false"
    debug_sign = hashlib.md5(f"false{DEBUG_RID}{DEBUG_TS}".encode()).hexdigest()
    check(debug_sign == DEBUG_SIGN, "sign mechanism debug sample",
          f"(MD5(\"false\"+rid+ts) = {debug_sign})")

    # 4. AES-128-CBC 响应解密 (2024-12-17 真实密文)
    dec = data_decode(AES_CIPHER)
    ok = all(dec.get(k) == v for k, v in AES_EXPECT.items())
    check(ok, "response AES decrypt",
          f"(address={dec.get('address')!r}, reportId={dec.get('reportId')}, state={dec.get('state')})")

    # 5. RSA 结构: 117 字符/块 -> 128B 密文/块 -> base64 长度公式
    pub = RSA.import_key(base64.b64decode(PUBLIC_KEY))
    check(pub.size_in_bits() == 1024 and (pub.size_in_bits() + 7 >> 3) - 11 == 117,
          "rsa key params", "(1024-bit, max block 117)")
    for n_chars in (117, 118, 234, 235, 300):
        body = rsa_encrypt_long("a" * n_chars)
        n_blocks = (n_chars + 116) // 117
        raw_len = 128 * n_blocks
        check(len(base64.b64decode(body)) == raw_len and len(body) == (raw_len + 2) // 3 * 4,
              f"rsa encryptLong structure ({n_chars} chars)",
              f"({n_blocks} blocks, {len(body)} b64 chars)")
        if n_chars == 118:
            check(len(base64.b64decode(body)) == 256, "block boundary at 118 chars",
                  "(2 blocks -> 256 bytes)")

    # 6. detail.js 详情 URL: param=Base64(JSON), sign 固定 = MD5("")
    url = record_url("9874d595-1e77-4089-917d-2368198d74ca", 1787157341936)
    expect_param = ("eyJyZXBvcnRJZCI6Ijk4NzRkNTk1LTFlNzctNDA4OS05MTdkLTIzNjgxOThkNzRj"
                    "YSIsInRzIjoxNzg3MTU3MzQxOTM2fQ==")
    ok = (f"https://www.birdreport.cn/home/record/page.html?param={expect_param}"
          f"&sign=d41d8cd98f00b204e9800998ecf8427e") == url
    check(ok, "detail page URL (node 实跑交叉验证)",
          f"(sign={url.rsplit('sign=', 1)[1]})")

    # 7. 真实请求全链 (--live): RSA body + sign headers -> HTTP 200 code:0 -> AES 解密
    if "--live" in sys.argv:
        import time
        rid = hashlib.md5(os.urandom(16)).hexdigest()
        body, sign, request_id, ts = header_data(data, rid, int(time.time() * 1000))
        req = urllib.request.Request(
            "https://api.birdreport.cn/front/record/activity/search",
            data=body.encode(), method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded",
                     "sign": sign, "timestamp": ts, "requestId": request_id,
                     "Referer": "https://www.birdreport.cn/",
                     "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                                    "Chrome/126.0.0.0 Safari/537.36")})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
            rows = data_decode(raw["data"])
            check(resp.status == 200 and raw.get("code") == 0 and len(rows) > 0,
                  "live request chain",
                  f"(HTTP {resp.status}, code={raw.get('code')}, count={raw.get('count')}, "
                  f"rows={len(rows)}, first end_time={rows[0].get('end_time')})")
        except Exception as e:
            check(False, "live request chain", f"({e})")
    else:
        print("[SKIP] --live real request (add --live, needs network + proxy)")

    print(f"\n{passed}/{total} passed")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
