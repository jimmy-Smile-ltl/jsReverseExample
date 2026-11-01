"""
pro38 去哪儿 机票 Bella 签名 — HmacSHA1 + 自定义 65 字母表 base64

复现 m.flight.qunar.com H5 机票搜索的 Bella 参数（零第三方依赖）:

    Bella = june_v ## sign ## cipher ## random21 ## keyArray

    v1: sign = HMAC-SHA1( JSON(params) + cipher + random21 + JSON(keyArray) )
    v2: sign = HMAC-SHA1( JSON(params) + random21 + JSON(keyArray) )      # 线上走 v2
        v2 再把 sign / randomNum / t 写进 envMap，一起加密成 cipher

    cipher  = 自定义 base64( encodeURIComponent(JSON(envMap)) )
              · 3 字节切 4 组 6bit；qunar/tujia 域下每个 6bit 取反 v = 63 - v
              · 映射 65 字符表（第 65 个字符是填充位，正常编码用不到）

来源: m.flight.qunar.com/h5/flight/ 的 webpack inline bundle（2026-10-31）。
      两组样例取自页面 window.Bella 的真实输出，本实现可逐字节重建。

用法:
    python main.py        # 运行内置样例，输出即验证
"""

import hashlib
import hmac
import json
import random
import time
from urllib.parse import quote, unquote

# ---------------------------------------------------------------- 常量（对齐 JS）
# 65 字符表；下标 0..63 参与编码，第 65 个字符留给填充
ALPHABET = ("B6F1YrNm+OA=sw" "n8xbeLlzQ" "p5M02SUHt/dog" "cyfj-9kPKu"
            "EX7VWaqJi" "3CIGDRhTv4")
assert len(ALPHABET) == 65 and len(set(ALPHABET)) == 65

HMAC_KEY = b"h8fsaK3wqe+ioMvs"       # CryptoJS HmacSHA1(input, Utf8.parse(key))
HEX62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def _b36(n: int) -> str:
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    if n == 0:
        return "0"
    out = ""
    while n:
        out = digits[n % 36] + out
        n //= 36
    return out


def _build_rand_alphabet() -> str:
    """页面 randomNum 用的 64 字符表: '-_' + 36..0 的 base36 + 35..10 的大写。"""
    s = "-_"
    for i in range(35, -1, -1):
        s += _b36(i)
    for i in range(35, 9, -1):
        s += _b36(i).upper()
    return s


RAND_ALPHABET = _build_rand_alphabet()
assert len(RAND_ALPHABET) == 64


# ---------------------------------------------------------------- 核心复现
def random21(rng=random) -> str:
    """JS randomNum(21): 从 64 字符表取 21 位（对应原函数 random21）。"""
    return "".join(RAND_ALPHABET[rng.randrange(64)] for _ in range(21))


def hmac_sha1_hex(data: str) -> str:
    """JS HmacSHA1: CryptoJS 输出 40 位小写 hex。"""
    return hmac.new(HMAC_KEY, data.encode("utf-8"), hashlib.sha1).hexdigest()


def js_encode_uri_component(s: str) -> str:
    """encodeURIComponent 等价: '/' 会被编码，!*'() 不编码；UTF-8 百分号编码。"""
    return quote(s, safe="!*'()")


def encode_payload(plaintext: str, invert: bool = True) -> str:
    """JS cipher(): encodeURIComponent → 空格补齐 3 的倍数 → 4×6bit → 字母表。"""
    s = js_encode_uri_component(plaintext)
    while len(s) % 3:
        s += " "
    out = []
    for i in range(0, len(s), 3):
        bits = "".join(format(ord(c), "08b") for c in s[i:i + 3])
        for j in range(0, 24, 6):
            v = int(bits[j:j + 6], 2)
            if invert:                     # 只有 qunar / tujia 域名命中取反
                v = 63 - v
            out.append(ALPHABET[v])
    return "".join(out)


def decode_payload(blob: str, invert: bool = True) -> str:
    """encode_payload 的逆运算（调试/自证用）。"""
    bits = []
    for ch in blob:
        v = ALPHABET.index(ch)
        if invert:
            v = 63 - v
        bits.append(format(v, "06b"))
    bits = "".join(bits)
    raw = bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits) - 7, 8))
    return unquote(raw.decode("latin-1"))


def build_env_map(env: dict) -> dict:
    """JS flatToMap(getEnvInfo()): 固定 8 键、固定顺序。"""
    order = ["referer", "piccolo", "shirley", "title", "keywords",
             "description", "host", "scriptSrc"]
    return {k: env.get(k, "") for k in order}


def json_canon(obj) -> str:
    """JSON.stringify 等价（无空格、保留非 ASCII）。"""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def make_bella(params: dict, june_v: str, env: dict, v2: bool = True,
               invert: bool = True, rng=random, now_ms: int = None) -> str:
    """JS Bella(params, {v: 2})：生成完整 5 段签名串。"""
    b_param = json_canon(params)
    key_array = list(params.keys())
    rand = random21(rng)
    flat = build_env_map(env)

    if not v2:
        # v1: cipher 参与 HMAC，sign 不写回明文
        enc = encode_payload(json_canon(flat), invert=invert)
        sign = hmac_sha1_hex(b_param + enc + rand + json_canon(key_array))
        return "##".join([june_v, sign, enc, rand, ",".join(key_array)])

    sign = hmac_sha1_hex(b_param + rand + json_canon(key_array))
    flat["sign"] = sign
    flat["randomNum"] = rand
    flat["t"] = now_ms if now_ms is not None else int(time.time() * 1000)
    enc = encode_payload(json_canon(flat), invert=invert)
    return "##".join([june_v, sign, enc, rand, ",".join(key_array)])


def parse_bella(bella: str) -> dict:
    parts = bella.split("##")
    return {
        "june_v": parts[0],
        "sign": parts[1],
        "cipher": parts[2],
        "random": parts[3],
        "key_array": parts[4].split(",") if len(parts) > 4 else [],
        "n_parts": len(parts),
    }


# ---------------------------------------------------------------- 样例验证
# 2026-10-31 页面 window.Bella 真值（params 为「北京 → 上海 2026-11-05 1 成人」）
PARAMS = {"departureCity": "北京", "arrivalCity": "上海",
          "departureDate": "2026-11-05", "adult": 1, "child": 0, "baby": 0}

ENV_V1 = {"referer": "", "piccolo": "5053##3FB7D3352F3FE51D##1793451187924",
          "shirley": "66968a8ca693474aba3a78a7d6de0452", "title": "去哪儿网机票服务",
          "keywords": ",去那儿,航班查询,", "description": "去哪儿(Qunar.com)飞机票,特价",
          "host": "m.flight.qunar.com", "scriptSrc": ["webresource.c-ct", "common.qunarzz.c"]}

ENV_V2 = {"referer": "", "piccolo": "2285##ED8CC60F6EA6D549##1793451187933",
          "shirley": "66968a8ca693474aba3a78a7d6de0452", "title": "去哪儿网机票服务",
          "keywords": ",去那儿,航班查询,", "description": "去哪儿(Qunar.com)飞机票,特价",
          "host": "m.flight.qunar.com", "scriptSrc": ["webresource.c-ct", "common.qunarzz.c"]}

BELLA_V1 = '1683616182042##b903aee4e35702cacb58afba284861b2effabe0b##iKohiK3wgMkMf-i0gUPwaUPsXuPwaUPwaUPwXwPwa5TQjOWxcI10aS30a=D0aS3AaRPsiK3siK3sa=fhW=XsasPwESWIEKPnEhPwawPwasD+VKa=WKDnVRgNaSX0aS30a2a0aSisyI0wcIkNiK3wiKWTiK3wWSjNWSHHVIWHWS2sWRg=j9iHaOD+VID+fRf2fKv=WK30aS30a2a0aSi=y-ELfuPwaUPsXuPwaUkGWuPmEukhXUkGWuPNawkTXukGWuPmWhkhEUkGWwkhEhPNaukGWUPNXwkhXukGWwkTWukTVhkGWUPNXwPmEhkGWuPmXukTauPwaUPwXwPwaMe0d-oxgMEsiK3wiKWTiK3wiKiRiPPAiKHGiPihiPPNiKtwiPDsiPPAiKt=iPiIiKiRiPPmiKtmiPGTiPP+iKHIiPGDiPPOiK0IiPDAiPPmiPGIiPDwiKiRiK3wiKiRiK3wfIksj+iQgCEQcOm0aS30a=D0aS30EKP0VDP0X230EKP0VKa0XPD0EKP0VRX0X2jpP-kbj-3bjOFeJukGVukTawPNEukGWUPNXwkhXukGWwkTWukTVhPwXwkGWwPmVukhVukGWhkhXUkhWwPwaUPwXwPwaMHxg+X0aS30a=D0aSieqMfLy9opohNno9NHgUNScO=0aS30a2a0aSisj+iQgCEKgMa0aS30a=D0WP30aSi+f9iwf-Wxo-iSfuNSq9W=iK3wiKiRiK3wjOFec9Fbq5GAcMGwd5pbjwPwaUPAEhP+Ehvt##LS4CSXlrN3EPLUXcGCbPu##departureCity,arrivalCity,departureDate,adult,child,baby'
BELLA_V2 = '1683616182042##a95fc55c711aac6163e0ba084cc9411040e4714f##iKohiK3wgMkMf-i0gUPwaUPsXuPwaUPwaUPwXwPwa5TQjOWxcI10aS30a=D0aS3waStAiK3siK3sEPXmX=aOaDjOEPDOERP=VuPwawPwasD+VKa=WKDnVRgNasa0aS30a2a0aSisyI0wcIkNiK3wiKWTiK3wWSjNWSHHVIWHWS2sWRg=j9iHaOD+VID+fRf2fKv=WK30aS30a2a0aSi=y-ELfuPwaUPsXuPwaUkGWuPmEukhXUkGWuPNawkTXukGWuPmWhkhEUkGWwkhEhPNaukGWUPNXwkhXukGWwkTWukTVhkGWUPNXwPmEhkGWuPmXukTauPwaUPwXwPwaMe0d-oxgMEsiK3wiKWTiK3wiKiRiPPAiKHGiPihiPPNiKtwiPDsiPPAiKt=iPiIiKiRiPPmiKtmiPGTiPP+iKHIiPGDiPPOiK0IiPDAiPPmiPGIiPDwiKiRiK3wiKiRiK3wfIksj+iQgCEQcOm0aS30a=D0aS30EKP0VDP0X230EKP0VKa0XPD0EKP0VRX0X2jpP-kbj-3bjOFeJukGVukTawPNEukGWUPNXwkhXukGWwkTWukTVhPwXwkGWwPmVukhVukGWhkhXUkhWwPwaUPwXwPwaMHxg+X0aS30a=D0aSieqMfLy9opohNno9NHgUNScO=0aS30a2a0aSisj+iQgCEKgMa0aS30a=D0WP30aSi+f9iwf-Wxo-iSfuNSq9W=iK3wiKiRiK3wjOFec9Fbq5GAcMGwd5pbjwPwaUPAEhPwXwPwa5WQfOm0aS30a=D0aSiHVKkMjsPAjsgna9GHjsjnWSW0aIiHaRt=jOaNWRDnaRX8fKX+aKEMiK3wiKiRiK3wgMGbfIFeK5keiK3wiKWTiK3wk-i/yCkOkSoGuI1wkAWEg+H/K0E9iK3wiKiRiK3wohPwaUPsXKD+VKa=WKDnVRgNasa0W=Xt##Ur_huvV7EHo2WSQsx_NTV##departureCity,arrivalCity,departureDate,adult,child,baby'   # 内含 sign / randomNum / t（t=1793451187933）

JUNE_V = "1683616182042"

SAMPLE_CASES = [
    {"name": "v1（910B）", "v2": False, "env": ENV_V1,
     "random": "LS4CSXlrN3EPLUXcGCbPu", "now_ms": 0, "expected": BELLA_V1},
    {"name": "v2（1090B）", "v2": True, "env": ENV_V2,
     "random": "Ur_huvV7EHo2WSQsx_NTV", "now_ms": 1793451187933,
     "expected": BELLA_V2},
]


class FixedRng:
    """把 random21 的取数钉死到已知序列，保证样例可复现。"""

    def __init__(self, s: str):
        self.s, self.i = s, 0

    def randrange(self, n: int) -> int:
        ch = self.s[self.i]
        self.i += 1
        return RAND_ALPHABET.index(ch)


def main() -> None:
    passed = 0
    for case in SAMPLE_CASES:
        got = make_bella(PARAMS, JUNE_V, case["env"], v2=case["v2"],
                         rng=FixedRng(case["random"]), now_ms=case["now_ms"])
        ok = got == case["expected"]
        passed += ok
        print("[%s] %s  len=%d" % ("PASS" if ok else "FAIL", case["name"], len(got)))
        if not ok:
            print("      expected: %s" % case["expected"][:120])
            print("      got     : %s" % got[:120])

    # 第三组: 反向解密 —— cipher 必须还原出含 sign/randomNum/t 的 envMap
    parsed = parse_bella(BELLA_V2)
    plain = json.loads(decode_payload(parsed["cipher"]))
    checks = [
        ("parts=5", parsed["n_parts"] == 5),
        ("sign 段 == 明文内 sign", parsed["sign"] == plain.get("sign")),
        ("random 段 == 明文 randomNum", parsed["random"] == plain.get("randomNum")),
        ("t 回填", plain.get("t") == 1793451187933),
    ]
    ok = all(v for _, v in checks)
    passed += ok
    print("[%s] cipher 反解: %s" % ("PASS" if ok else "FAIL",
                                   ", ".join(k for k, v in checks if v)))

    print("\n%d/%d 通过" % (passed, len(SAMPLE_CASES) + 1))
    if passed != len(SAMPLE_CASES) + 1:
        raise SystemExit(1)


# ---------------------------------------------------------------- 可选: 真实请求验证
# 真实请求（需网络，不进入 main）:
#   POST https://m.flight.qunar.com/api/touchInnerList
#   body: departureCity=北京&arrivalCity=上海&departureDate=...&Bella=<上面生成>&_v=2
# 注意: 服务端数据层对部分出口 IP 软屏蔽（恒 code:1999 空结果），签名对不对以
#       「同参数下真 Chrome 是否同样空」为准，不要用返回条数判断签名正确性。

if __name__ == "__main__":
    main()
