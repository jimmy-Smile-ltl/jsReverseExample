"""
酷狗音乐 (www.kugou.com) — 短信登录加密: signature + RSA-1024 NoPadding (+ 定制 AES 走 Node)

用法:
    python main.py            # 纯 Python 验证 signature/RSA/mid/请求组装 (无需网络)
    python main.py --node     # 追加: Node 交叉验证 (RSA 独立实现 + 提取的 CryptoJS 模块)

原理 (kguser.v2.min.js):
    POST /v8/send_mobile_code?appid=1014&clientver=1000&clienttime={ms}&mid={md5}
        &uuid={md5}&dfid={dfid}&srcappid=2919&signature={sig}
    body: {"plat":4,"clienttime_ms":{ms},"businessid":5,"pk":{RSA},"params":{AES},"mobile":"13********8"}

    1. signature = MD5(salt + 排序 key=value 无分隔拼接 + JSON body + salt).upper()
         salt = "NVPh5oo715z5DIWAeQlhMDsWXXQV4hwt"
    2. pk = RSA-1024 NoPadding: 明文 JSON 反转 -> 前导零补到 128 字节 -> little-endian
         解释 -> pow(m, 0x10001, n) -> 256 hex (与浏览器逐位一致)
    3. params = 定制 AES-128-CBC (CryptoJS 自有实现, 标准 AES 输出被服务器拒绝!)
         已提取原始模块 kugou_aes_module.js 纯 JS 运行 -> Node 桥接
    4. mid = MD5(uuid).upper()  (uuid 与 mid 同值)

样例来源: AES 期望值 = 2026-06-29 浏览器实测 (README 6.2 对照实验);
         signature 算法原项目对真实抓包签名验证通过 (0D92E57B... ✓ MATCH, 2026-06-29)
"""

import hashlib
import json
import os
import subprocess
import sys
import urllib.parse

SIGNATURE_SALT = "NVPh5oo715z5DIWAeQlhMDsWXXQV4hwt"
RSA_N = int(
    "B1B1EC76A1BBDBF0D18E8CD9A87E53FA3881E2F004C67C9DDA2CA677DBEFA3D6"
    "1DF8463FE12D84FF4B4699E02C9D41CAB917F5A8FB9E35580C4BDF97763A0420A"
    "476295D763EE10174E6F9EBF7DF8A77BA5B20CDA4EE705DEF5BBA3C88567B9656"
    "E52C9CD5CD95CA735FF2D25F762B133273EEEB7B4F3EA8B6DA29040F3B67CD", 16)
RSA_E = 0x10001


def generate_signature(url_params: dict, post_data: dict = None) -> str:
    """signature = MD5(salt + 排序 key=value(无分隔) + JSON body + salt).upper()

    对应 kguser.v2.min.js getInterFaceKguser: K.unshift(salt), K.push(salt);
    body 为空 (falsy) 时整段省略。
    """
    parts = [SIGNATURE_SALT]
    for key in sorted(url_params.keys()):
        parts.append(f"{key}={url_params[key]}")
    if post_data:
        parts.append(json.dumps(post_data, separators=(",", ":")))
    parts.append(SIGNATURE_SALT)
    return hashlib.md5("".join(parts).encode("utf-8")).hexdigest().upper()


def rsa_encrypt_pk(aes_key: str, clienttime_ms: int) -> str:
    """RSA-1024 NoPadding -> 256 hex (对应 JS RSA.encrypt O 函数)

    字节布局 (关键): payload 反转后置于末尾, 前导零补足 128 字节,
    整体按 little-endian 16-bit 字解释 (等价 int.from_bytes(ba, 'little')).
    """
    payload = json.dumps({"clienttime_ms": clienttime_ms, "key": aes_key},
                         separators=(",", ":"))
    pb = payload.encode("utf-8")
    byte_array = b"\x00" * (128 - len(pb)) + pb[::-1]
    m = int.from_bytes(byte_array, "little")
    return format(pow(m, RSA_E, RSA_N), "x").zfill(256)


def gen_mid(uuid: str) -> str:
    """mid = MD5(uuid).upper()"""
    return hashlib.md5(uuid.encode("utf-8")).hexdigest().upper()


def node_aes_encrypt(plaintext: str, fixed_key: str = None) -> dict:
    """定制 AES: 运行提取的 CryptoJS 模块 (kugou_aes_module.js)"""
    cli = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kg_aes_ref.js")
    cmd = ["node", cli, plaintext] + ([fixed_key] if fixed_key else [])
    out = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def build_send_mobile_request(mobile: str, random_key: str, clienttime_ms: int,
                              uuid: str, dfid: str, params: str = None) -> dict:
    """组装完整 send_mobile_code 请求 (对应 GetSmsCode); params 缺失时走 Node"""
    if params is None:
        params = node_aes_encrypt(json.dumps({"mobile": mobile},
                                             separators=(",", ":")))["encryptedStr"]
    pk = rsa_encrypt_pk(random_key, clienttime_ms)
    mid = gen_mid(uuid)
    url_params = {"appid": 1014, "clientver": 1000, "clienttime": clienttime_ms,
                  "mid": mid, "uuid": uuid, "dfid": dfid, "srcappid": 2919}
    post_data = {"plat": 4, "clienttime_ms": clienttime_ms, "businessid": 5,
                 "pk": pk, "params": params,
                 "mobile": mobile[:2] + "*" * 8 + mobile[-1]}
    signature = generate_signature(url_params, post_data)
    url_params["signature"] = signature
    return {"url": "https://gateway.kugou.com/v8/send_mobile_code?"
                   + urllib.parse.urlencode(url_params),
            "body": json.dumps(post_data, separators=(",", ":")),
            "signature": signature}


# ============================================================ 样例验证

# 1. RSA 固定明文期望值 (2026-06-29 与浏览器逐位一致验证)
RSA_EXPECT = ("46128358676ea6cff631cdc06d7d25c1a33c6c428afbb2eda8605e8ea00b69a0"
              "5cb59f738f5cb9f70685a85a79f8ad52078e8e44bfd5631086f7133a123c5001c"
              "c12691f286650b56d2e7e27716aaa49e0643c4b6868713a3b4825f60a4882da29"
              "2d4c69b6e0da12e9d608df28ae34845cb01c93bc8d399719f67cc14f5fc4fe")

# 2. signature 结构期望 (固定 URL 参数, 无 body)
SIG_URL_PARAMS = {"appid": 1014, "clientver": 1000, "clienttime": 1782730020678,
                  "mid": "26268217e5505d50265a6caa7d1ccd4a",
                  "uuid": "26268217e5505d50265a6caa7d1ccd4a",
                  "dfid": "1u0fIr3ZU0xe2Znq3L3dY6xw", "srcappid": 2919}
SIG_EXPECT = "1BFA0E32D1C9154840E9C2F7CC2AED59"

# 3. 定制 AES 浏览器实测期望值 (2026-06-29 对照实验: 固定 key, CryptoJS 原始模块输出)
AES_FIXED_KEY = "5SO2VCRF8O81PJH3"
AES_PLAINTEXT = '{"mobile":"13812345678"}'
AES_EXPECT = "d4f624c0c69e718c0007800aea95afc786364a32abd45480ff4975d0bd3caa5e"


def main() -> None:
    passed = 0
    total = 0

    def check(ok: bool, label: str, detail: str = "") -> None:
        nonlocal passed, total
        total += 1
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label} {detail}")

    # 1. RSA-1024 NoPadding: 固定明文期望值
    got = rsa_encrypt_pk("5SO2VCRF8O81PJH3", 1782730020678)
    check(got == RSA_EXPECT, "RSA pk fixed payload", f"(len {len(got)})")

    # 2. signature: 固定参数期望值 + 确定性 + body 参与
    sig = generate_signature(SIG_URL_PARAMS)
    check(sig == SIG_EXPECT and sig == generate_signature(SIG_URL_PARAMS),
          "signature structure", f"({sig})")
    sig_body = generate_signature(SIG_URL_PARAMS, {"plat": 4, "clienttime_ms": 1782730020678})
    check(sig_body != sig, "signature includes body", f"({sig_body[:24]}...)")

    # 3. mid = MD5(uuid).upper()
    check(gen_mid("26268217e5505d50265a6caa7d1ccd4a") == "D845247C779F078318D1C4E6075CCE11",
          "mid = MD5(uuid)", f"({gen_mid('26268217e5505d50265a6caa7d1ccd4a')})")

    # 4. 完整请求组装 (params 用浏览器实测密文常量, 无需 Node)
    req = build_send_mobile_request("13812345678", "5SO2VCRF8O81PJH3", 1782730020678,
                                    "26268217e5505d50265a6caa7d1ccd4a",
                                    "1u0fIr3ZU0xe2Znq3L3dY6xw", params=AES_EXPECT)
    body = json.loads(req["body"])
    ok = (req["url"].startswith("https://gateway.kugou.com/v8/send_mobile_code?")
          and "signature=" in req["url"] and body["mobile"] == "13********8"
          and len(body["pk"]) == 256 and body["params"] == AES_EXPECT)
    check(ok, "request assembly", f"(url len {len(req['url'])}, body len {len(req['body'])})")

    # 5. Node 交叉验证 (可选)
    if "--node" in sys.argv:
        # 5a. 定制 AES: 提取的 CryptoJS 模块, 固定 key -> 与浏览器实测一致
        aes = node_aes_encrypt(AES_PLAINTEXT, AES_FIXED_KEY)
        check(aes["encryptedStr"] == AES_EXPECT, "AES node vs browser", f"(key {aes['key']})")
        # 5b. RSA 独立实现 (rsa_ref.js)
        cli = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rsa_ref.js")
        out = subprocess.run(["node", cli, "5SO2VCRF8O81PJH3", "1782730020678"],
                             capture_output=True, text=True, check=True)
        check(out.stdout.strip() == RSA_EXPECT, "RSA node cross-check", f"(len {len(out.stdout.strip())})")
        # 5c. 完整请求: params 现场由 Node 生成
        req2 = build_send_mobile_request("13812345678", "5SO2VCRF8O81PJH3",
                                         1782730020678, "26268217e5505d50265a6caa7d1ccd4a",
                                         "1u0fIr3ZU0xe2Znq3L3dY6xw")
        body2 = json.loads(req2["body"])
        check(len(body2["params"]) == 64 and body2["params"] != AES_EXPECT,
              "request with live node params", f"(len {len(body2['params'])})")
    else:
        print("[SKIP] --node cross-check (add --node for AES CryptoJS module + RSA)")

    print(f"\n{passed}/{total} passed")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
