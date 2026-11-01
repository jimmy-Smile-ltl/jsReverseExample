"""
pro40 途家 Revelio 风控报文 — 字符串表轮转还原 AES-GCM 密钥

m.tujia.com 的风控 SDK（webpack chunk-2d0c5538）在上报时发出:

    {"appCode":"fetujia_mob","platform":"web","version":"1.0.0",
     "data":{"iv":b64(12B), "salt":b64(16B), "type":0, "txt":b64(AES-GCM)}}

密钥不是明文常量，而是被折叠进「29 项字符串表 + 26 次轮转」的索引引用里:

    A(n)    = R()[n - 211]
    P[KEY]  = "sFOhW/1xnw3PbXr6AhvS+OICOP6uti" + A(215) + "Pe5uZ7ZZZM" + A(218)
              + A(233) + A(228) + A(239) + A(224) + A(213) + A(230)
              + "pyblQmj1MeVLzCi+K188" + A(212) + "n/T86A6uW0" + A(219) + A(225)
              + "3rTcKZ+Prb" + A(232) + A(223) + A(237)        # 218 字符
    KEY     = P[KEY].slice(32, 64)                              # 32 字节 ASCII

轮转次数由 IIFE 里的校验式决定（parseInt 语义: 取前导数字，无数字为 NaN）:
    207590 === parseInt(A(221))/1*(parseInt(A(217))/2) + parseInt(A(216))/3
             + -parseInt(A(234))/4 + -parseInt(A(235))/5*(-parseInt(A(214))/6)
             + parseInt(A(220))/7*(-parseInt(A(231))/8) + parseInt(A(226))/9
             + -parseInt(A(222))/10*(parseInt(A(238))/11)

来源: https://m.tujia.com chunk-2d0c5538（Revelio SDK）
      2026-10-31 用真机抓包 52,521B 报文解密验证，随后纯算法换 token 打通业务接口。
依赖: cryptography（AES-GCM）。其余为标准库。
用法: python main.py
"""

import base64
import copy
import json
import os
import random
import time

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ---------------------------------------------------------------- 字符串表复原
# SDK 里 R() 的原始顺序（29 项）
_STRINGS = ["6KIjDXy", "J5JeYNb41m", "355923BQpTim", "278274OImimj",
            "Unu34Xz4BO", "oC+mJHwOLn", "7Lpvqxo", "1GtGfUP", "110rtquQN",
            "1C1tHZFza2", "OLBh1K9ufc", "P8HKN0q2Fu", "2271339oKPeQU", "1.0.0",
            "6NvNNi1NYs", "abc", "HDgsP+6RDF", "1238152qonLgv", "s/dcBHaWJi",
            "G1MdPdG5kA", "1300940LorJLS", "1181035UBVEmB", "REPORT_URL",
            "O+1gUQTg", "58762IqfkmW", "TX87dLU9Jg", "salt", "7mUsjcyppa",
            "2WK5uwwgsv"]

# P[KEY] 的拼装顺序: 字面片段与取表下标交替，对应 SDK 里的 "+ A(215) + ..."
_KEY_RECIPE = [
    ("lit", "sFOhW/1xnw3PbXr6AhvS+OICOP6uti"),
    ("ref", 215), ("lit", "Pe5uZ7ZZZM"),
    ("ref", 218), ("ref", 233), ("ref", 228), ("ref", 239), ("ref", 224),
    ("ref", 213), ("ref", 230),
    ("lit", "pyblQmj1MeVLzCi+K188"),
    ("ref", 212), ("lit", "n/T86A6uW0"),
    ("ref", 219), ("ref", 225), ("lit", "3rTcKZ+Prb"),
    ("ref", 232), ("ref", 223), ("ref", 237),
]


def js_parse_int(s: str):
    """JS parseInt(x) 的最小等价: 去空白/符号前缀，取连续数字，无数字为 NaN。"""
    s = s.lstrip()
    sign, i = 1, 0
    if s[:1] in "+-":
        sign = -1 if s[0] == "-" else 1
        i = 1
    j = i
    while j < len(s) and s[j] in "0123456789":
        j += 1
    if j == i:
        return float("nan")
    return sign * int(s[i:j])


def _rotation_expr(table) -> float:
    """IIFE 里的校验式；table 是当前轮转状态。"""
    def A(n):
        return js_parse_int(table[n - 211])
    return (A(221) / 1 * (A(217) / 2) + A(216) / 3 + -A(234) / 4
            + -A(235) / 5 * (-A(214) / 6) + A(220) / 7 * (-A(231) / 8)
            + A(226) / 9 + -A(222) / 10 * (A(238) / 11))


def rotate_table(target: int = 207590):
    """按 JS 的 `for(;;){ if(校验式) break; push(shift()) }` 逐次轮转。"""
    table = list(_STRINGS)
    for rounds in range(len(table) + 1):
        try:
            if _rotation_expr(table) == target:
                return table, rounds
        except (ValueError, TypeError):
            pass
        table.append(table.pop(0))
    raise RuntimeError("未命中轮转校验式")


def recover_key_material(table=None) -> str:
    """拼回 218 字符的 P[KEY] 串。"""
    table = TABLE if table is None else table
    return "".join(v if kind == "lit" else table[v - 211]
                   for kind, v in _KEY_RECIPE)


TABLE, ROTATIONS = rotate_table()
KEY_MATERIAL = recover_key_material()
KEY = KEY_MATERIAL[32:64].encode("ascii")


# ---------------------------------------------------------------- 报文生成/解析
def new_tuid() -> str:
    """设备号 = uuid4 形态 + '-' + 13 位毫秒（服务端不校验取值）。"""
    s = "".join(random.choice("0123456789abcdef") for _ in range(32))
    u = "%s-%s-4%s-%s%s-%s" % (s[:8], s[8:12], s[13:16],
                               "89ab"[random.randint(0, 3)], s[17:20], s[20:32])
    return "%s-%d" % (u, int(time.time() * 1000))


def encrypt(plain: dict, iv: bytes = None, salt: bytes = None) -> dict:
    """AES-GCM 加密分支（type=0，有 WebCrypto 的浏览器走这条）。"""
    iv = iv if iv is not None else os.urandom(12)
    salt = salt if salt is not None else os.urandom(16)
    txt = AESGCM(KEY).encrypt(iv, json.dumps(plain, separators=(",", ":")).encode(), None)
    return {"iv": base64.b64encode(iv).decode(),
            "salt": base64.b64encode(salt).decode(),
            "type": 0,
            "txt": base64.b64encode(txt).decode()}


def decrypt(data: dict) -> dict:
    """解密上报体（data 段或整个 body 都接受），用于校验/取证。"""
    d = data.get("data", data)
    iv = base64.b64decode(d["iv"])
    return json.loads(AESGCM(KEY).decrypt(iv, base64.b64decode(d["txt"]),
                                          d.get("aad")).decode())


def build_body(template: dict, tuid: str = None, cookies: str = None,
               ts: float = None) -> dict:
    """把模板的时间基准平移到 ts，并替换设备号 / cookie 串。"""
    p = copy.deepcopy(template)
    now = ts if ts is not None else time.time() * 1000
    base = p.get("ts") or now
    p["ts"] = now
    for k in ("str", "end"):
        if isinstance(p.get(k), (int, float)):
            p[k] = now - base + p[k]

    def shift(node):
        if isinstance(node, dict):
            for kk, vv in node.items():
                if kk in ("str", "end") and isinstance(vv, (int, float)):
                    node[kk] = now - base + vv
                else:
                    shift(vv)
        elif isinstance(node, list):
            for it in node:
                shift(it)

    for k in ("sft", "hrd", "usr", "ufp", "wgl", "env", "nd", "at"):
        if k in p:
            shift(p[k])

    if tuid:
        ufp = p.setdefault("ufp", {})
        t = ufp.get("tuid")
        if isinstance(t, dict):
            t["raw"] = t["sh"] = tuid
        else:
            ufp["tuid"] = {"spt": True, "raw": tuid, "sh": tuid,
                           "str": now, "end": now + 0.3}
    if cookies is not None:
        p.setdefault("env", {})["ck"] = cookies
    return p


def build_payload(template: dict, tuid: str = None, cookies: str = None,
                  ts: float = None) -> str:
    """完整上报体 JSON 字符串（POST /revelio/report）。"""
    return json.dumps({"appCode": "fetujia_mob", "platform": "web",
                       "version": "1.0.0",
                       "data": encrypt(build_body(template, tuid, cookies, ts))},
                      separators=(",", ":"))


# ---------------------------------------------------------------- 样例验证
FIXED_PLAIN = {
    "ts": 1793453412631.0, "str": 12.5, "end": 345.2,
    "sft": {"u": "Mozilla/5.0 (Linux; Android 13) Chrome/138.0.0.0 Mobile Safari/537.36",
            "v": "", "pf": "Linux armv8l", "ud": ""},
    "hrd": {"sr": "411x823x2", "c": "a1b2c3d4", "m": 8},
    "usr": {"lg": "zh-CN", "tz": "Asia/Shanghai", "cp": 8},
    "ufp": {"tuid": {"raw": "864a0845-70af-4ed9-a9dc-ad40da74149c-1793453412631",
                     "sh": "864a0845-70af-4ed9-a9dc-ad40da74149c-1793453412631"},
            "cva": "e3b0c44298fc1c14", "cvb": "9f86d081884c7d65"},
    "wgl": {"rdr": "Qualcomm", "vdr": "Adreno (TM) 640"},
    "env": {"crm": 0, "ck": ""}, "nd": {}, "at": {},
}
FIXED_IV = bytes(range(12))
FIXED_SALT = bytes(range(16))

# 固定 iv/salt/plainttext 下的确定性密文（AES-GCM 本身是随机的，钉死 input 才可复现）
EXPECTED_TXT = ("y/qkZjdmHYe9wv54389XjW/030Spms+PKZK4g4mQXGvUC25hUHjD8LQs2LMAZ0XXr"
                "Uh1ND96gDxDu8ci8l9eaBV4D8bc9n5fLvp5SXIBiPrwjDMA2jBm0+WrgVbkM48ji6"
                "i9+Q5mEn1OTzPTCwKNRX67kTQY1Ncqll1uuZYuCGcnfcgL34Z4Y4DEOz7/aUyY8ZDumo"
                "8PLjhqHBXyPD9lv6KLF2tYjRIOha+/TzkvllfOxMApjuNVfqIrqyNrQyyx48YJ8euJB4"
                "qrDe2WIKj0A8V08YOWgIPdru9ePCqByL/u21KJdqBJCEJU2CaHftccS97+9Gqw/KoS/u9b"
                "hCHklmiXZTL+xQfG7hCl2WRqh6G1MKXwBQRgr2YT63Tj2jOoznejx9uP26/PiO25P8vURc"
                "lK4s1HK2MlLEXp03sbu/2CbwGGsdjVQxtER/tlVUU9UKjrruwIqgQejoWWNSDszLXqZEwB"
                "CuGFHaXV/qHwbDXfLe5VtwYe3O2uLPoyl5lpU0t7CCNnzwX1fQYeZnJusafg11LzyobmNc"
                "525J46whTjDXl6AGdYCB/FQc7IMGnslZaouA8jKjLAoSk1NCdSZOCkeHiubY9QX7EAPWEU"
                "bx7MxlIOAdGXNr0wdZt3DH8hkFAstKA2eAqbsGKnstX4XY3/xyA7I/FAnzMZzJTjVA+c1"
                "j3/Pu/Gy4HLO0eVIYc2Hoqw08/X7IKAdgXPgZNOiddocdw=")

SHIFT_TEMPLATE = {"ts": 1000.0, "str": 10, "end": 20,
                  "sft": {"str": 5, "u": "x"}, "ufp": {"tuid": {"raw": "old"}}}

SAMPLE_CASES = [
    {"kind": "key", "name": "字符串表 26 次轮转还原密钥"},
    {"kind": "encrypt", "name": "AES-GCM 加密（固定 iv/salt）"},
    {"kind": "decrypt", "name": "AES-GCM 解密回环"},
    {"kind": "shift", "name": "指纹模板时间平移 + 设备号替换"},
]


def main() -> None:
    passed = 0

    ok = (ROTATIONS == 26 and len(KEY_MATERIAL) == 218
          and KEY.decode() == "JeYNb41mPe5uZ7ZZZMUnu34Xz4BOG1Md")
    passed += ok
    print("[%s] %s → 轮转 %d 次，%d 字符，KEY=%s" %
          ("PASS" if ok else "FAIL", SAMPLE_CASES[0]["name"], ROTATIONS,
           len(KEY_MATERIAL), KEY.decode()))

    box = encrypt(FIXED_PLAIN, FIXED_IV, FIXED_SALT)
    ok = box["txt"] == EXPECTED_TXT and box["iv"] == "AAECAwQFBgcICQoL" \
        and box["salt"] == "AAECAwQFBgcICQoLDA0ODw==" and box["type"] == 0
    passed += ok
    print("[%s] %s → %d 字节密文" % ("PASS" if ok else "FAIL",
                                     SAMPLE_CASES[1]["name"], len(box["txt"])))

    ok = decrypt(box) == FIXED_PLAIN
    passed += ok
    print("[%s] %s" % ("PASS" if ok else "FAIL", SAMPLE_CASES[2]["name"]))

    body = build_body(SHIFT_TEMPLATE, tuid="new-tuid", ts=5000)
    ok = (body["ts"] == 5000 and body["str"] == 4010 and body["end"] == 4020
          and body["sft"]["str"] == 4005 and body["ufp"]["tuid"]["raw"] == "new-tuid"
          and SHIFT_TEMPLATE["ts"] == 1000.0)   # 模板本身不被改动
    passed += ok
    print("[%s] %s → ts=5000 str=4010 end=4020 sft.str=4005" %
          ("PASS" if ok else "FAIL", SAMPLE_CASES[3]["name"]))

    print("\n%d/%d 通过" % (passed, len(SAMPLE_CASES)))
    if passed != len(SAMPLE_CASES):
        raise SystemExit(1)


# ---------------------------------------------------------------- 可选: 真实请求
# 完整链路（需网络，不进入 main）:
#   1) uuid/sid 本地生成 → POST /feapi/abtest/abtest/getbuckets（body []）登记身份
#   2) 用真实解密得到的指纹模板 build_payload() → POST /revelio/report → token
#   3) Cookie: _tujia_rvl_ = token|device_id|<ms>；之后业务接口直连
# 模板（39.8KB）含真实 cookie/画布哈希，不入库；按 _revelio_plain.json 结构自建即可。

if __name__ == "__main__":
    main()
