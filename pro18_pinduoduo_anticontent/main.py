"""
拼多多 (pinduoduo.com) — anti_content 参数: 自定义二进制序列化 + zlib + RC4 + base64url

用法:
    python main.py           # 结构/分层/密钥流样例验证 (纯 Python, 无网络)
    python main.py --node    # 追加 Node 补环境全链路验证 (需 node, generator/ 已自带引擎)
    python main.py --live    # 追加真实 API 请求验证 (需 --node + 网络)

原理 (调用链: 页面 getGoods() -> TPp2.a() -> fbeZ.messagePackSync(), 85KB 混淆引擎):
    Step A: 自定义二进制序列化 312B (pure_algo.py 对照抓包逐段还原, 2026-06-07):
        [0:5] 03 01 00 00 01 (格式版本+保留头) | [5:8] "28+" 类型标记
        | URL | 0x00 | FLOAT_DATA 49 15 2a 96 40 80 0f 88 08 | BIN_48_1B 48 1b
        | device_id (16 位随机数字) | '-' | timestamp (10 位数字)
        | BIN_50_80 50 80 40 58 59 | BIN_E1_DB e1 db cc 61 79 69 79
        | variant 71 7e/e9/7f | XO_MARKER 78 6f | UA 字符串
        | 80 28 + SIGNATURE (39B) | 88 28 + SIGNATURE | TAIL a9 02 b6 01 9e a2 4f ce 75 d0 00
        SIGNATURE = "XpmJX0CqlpdJX5PbnT__2~8b1uSw2S162cZb3Sp9" (浏览器捕获, 固定)
    Step B: zlib deflate level 9 -> 270B, 头恒为 78 DA (pako 默认 = zlib 格式带头)
    Step C: RC4 流加密 -> ~279B, 密文头恒为 D1 AA; 密钥由 device_id+timestamp 在
        fbeZ 引擎内派生, 未逆向 -> 纯 Python 只能复现 A/B/D + 密钥流 XOR 自证
    Step D: base64 URL-safe (+->-, /->_, 去=) -> anti_content 372~378 chars

    服务端校验需要 Step C 的真实输出 => 有效 anti_content 必须让原版引擎自己生成:
    Node 补环境 (generator/) 模拟浏览器 API + mock 掉 s6vS HTTP (无网络依赖),
    加载原版 webpack (webpack.js -> main.js -> subject.js), 原项目 2026-06-07
    实测 HTTP 200, 本仓库 2026-08-20 复测 200.

样例来源: 密钥流三元组 = 原项目 2026-06-07 插桩 (zlib 明文/RC4 密文/密钥流 XOR);
          抓包前缀 = 原项目文档实存 anti_content 片段 (2026-06-07, 均为截断);
          SIGNATURE 与二进制常量 = pure_algo.py 重构对照 (2026-06-07 浏览器捕获).
"""

import base64
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
import zlib

DIR = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(DIR, "generator")

# ---------- 二进制格式常量 (2026-06-07 抓包, pure_algo.py 重构) ----------
SIGNATURE = b"XpmJX0CqlpdJX5PbnT__2~8b1uSw2S162cZb3Sp9"
HEADER = bytes([0x03, 0x01, 0x00, 0x00, 0x01])
STR_TYPE = b"28+"
FLOAT_DATA = bytes([0x49, 0x15, 0x2A, 0x96, 0x40, 0x80, 0x0F, 0x88, 0x08])
BIN_48_1B = bytes([0x48, 0x1B])
BIN_50_80 = bytes([0x50, 0x80, 0x40, 0x58, 0x59])
BIN_E1_DB = bytes([0xE1, 0xDB, 0xCC, 0x61, 0x79, 0x69, 0x79])
XO_MARKER = bytes([0x78, 0x6F])
SIG_TYPE1 = bytes([0x80, 0x28])
SIG_TYPE2 = bytes([0x88, 0x28])
TAIL = bytes([0xA9, 0x02, 0xB6, 0x01, 0x9E, 0xA2, 0x4F, 0xCE, 0x75, 0xD0, 0x00])
VARIANTS = (0x7E, 0xE9, 0x7F)
URL = "https://www.pinduoduo.com/home/girlclothes/"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36")

# (zlib 明文头, RC4 密文头, 密钥流) — 2026-06-07 插桩样例, XOR 三向自证
KEYSTREAM_CASES = [
    ("78da636664606034", "d1aa807f1e5e3300", "a970e3197a3e5334"),
]

# 抓包实存 anti_content 片段 (2026-06-07, 文档截断) — 均以 "0aq" 开头 => 密文头 D1 AA
AC_SAMPLES = [
    "0aqWfxUkM_VeTpJyXbKtpFKccGEGqNojqoPYgO1Ywu5oWdNET8XQnxvQCdXK1YFSTqpUn_5",
    "0aqWtxUkM_VetfifdWBoeT1jiKGZOSOSvYAL",
    "0aqWtxUkM_VeTpjynbKGpFKccXEXqNojqofYsO1Ywu5oWdNE",
]

API_URL = "https://apiv2.pinduoduo.com/api/gindex/tf/query_tf_goods_info"
TF_ID = "TFRQ0v00000Y_13396"


# ---------- Step A: 自定义二进制序列化 ----------

def build_binary_payload(device_id: str, timestamp: str, variant: int) -> bytes:
    """312B 固定结构: 常量段 + device_id/timestamp/variant 可变段 (URL/UA 取默认)"""
    parts = [
        HEADER, STR_TYPE, URL.encode(), b"\x00", FLOAT_DATA, BIN_48_1B,
        device_id.encode(), b"-", timestamp.encode(), BIN_50_80, BIN_E1_DB,
        bytes([0x71, variant]), XO_MARKER, UA.encode(),
        SIG_TYPE1, SIGNATURE, SIG_TYPE2, SIGNATURE, TAIL,
    ]
    return b"".join(parts)


# ---------- Step D: base64 URL-safe (拼多多变体) ----------

def pdd_base64_encode(data: bytes) -> str:
    """+ -> -, / -> _, 去 = 填充"""
    return base64.b64encode(data).decode().replace("+", "-").replace("/", "_").rstrip("=")


def pdd_base64_decode(encoded: str) -> bytes:
    """逆变换, 补 = 填充"""
    padded = encoded.replace("-", "+").replace("_", "/")
    padded += "=" * (-len(padded) % 4)
    return base64.b64decode(padded)


# ---------- Node 补环境全链路 (generator/) ----------

def generate_node() -> str:
    """node generator/generate.js --json -> anti_content (s6vS HTTP 已 mock, 无网络)"""
    out = subprocess.run(
        ["node", os.path.join(GEN, "generate.js"), "--json"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=90, check=True)
    line = next(l for l in out.stdout.splitlines() if l.strip().startswith('{"success"'))
    return json.loads(line)["anti_content"]


def check_anti_content_shape(ac: str, full: bool = True) -> tuple:
    """形状不变量: 0aq 魔数 / base64url 字符集 / 解码头 D1 AA; full 时再查长度 372~378
    (抓包文档样例为截断片段, full=False)"""
    if not ac.startswith("0aq") or len(ac) < 4:
        return False, "(magic)"
    if full and (len(ac) < 370 or len(ac) > 385):
        return False, f"(len {len(ac)})"
    if any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
           for c in ac):
        return False, "(charset)"
    raw = pdd_base64_decode(ac)
    if raw[:2] != b"\xd1\xaa":
        return False, f"(header {raw[:2].hex()})"
    return True, f"(len {len(ac)}, header {raw[:2].hex()})"


def live_request(ac: str) -> tuple:
    """真实 API 请求: 返回 (status, success, goods_count, 首个商品名)"""
    params = {"tf_id": TF_ID, "page": "1", "size": "3", "anti_content": ac}
    url = API_URL + "?" + urllib.parse.urlencode(params)
    headers = {
        "Accept": "application/json, text/javascript",
        "Origin": "https://www.pinduoduo.com",
        "Referer": "https://www.pinduoduo.com/",
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/148.0.0.0 Safari/537.36"),
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        status = resp.status
        data = json.loads(resp.read().decode("utf-8"))
    goods = data.get("result") or []
    name = goods[0].get("goods_name", "") if goods else ""
    return status, data.get("success") is True, len(goods), name


# ---------- 主流程 ----------

def main() -> None:
    passed, total = 0, 0

    def check(ok: bool, label: str, detail: str = "") -> None:
        nonlocal passed, total
        total += 1
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label} {detail}")

    # 1. generator/ 文件齐备 + loader 本地化 patch + webpack patch 目标
    gen_files = ["env.js", "mocks.js", "loader.js", "generate.js",
                 "webpack.js", "main.js", "subject.js", "regenerator-runtime.js"]
    ok = all(os.path.isfile(os.path.join(GEN, f)) for f in gen_files)
    check(ok, "generator artifacts", f"({sum(os.path.getsize(os.path.join(GEN, f)) for f in gen_files)} bytes)")
    loader_src = open(os.path.join(GEN, "loader.js"), encoding="utf-8").read()
    check("[本地化 patch]" in loader_src and loader_src.count("[本地化 patch]") == 2,
          "loader localized patches", "(bundles dir + vendored regenerator-runtime)")
    webpack_src = open(os.path.join(GEN, "webpack.js"), encoding="utf-8").read()
    check("var p=i;t()" in webpack_src, "webpack runtime patch target",
          "(__webpack_require__ 暴露点)")

    # 2. 二进制 payload 结构: 固定输入 -> 312B 逐字节一致 + 关键字段格式
    #    偏移按常量动态计算 (HEADER 5 + "28+" 3 + URL 43 + 0x00 1 + FLOAT 9 + BIN 2)
    dev_off = len(HEADER) + len(STR_TYPE) + len(URL.encode()) + 1 \
        + len(FLOAT_DATA) + len(BIN_48_1B)
    ts_off = dev_off + 16 + 1
    for i, (dev, ts, var) in enumerate([("1234567890123456", "1787156125", 0x7E),
                                        ("0987654321098765", "1787156209", 0xE9),
                                        ("1122334455667788", "1787156300", 0x7F)]):
        p = build_binary_payload(dev, ts, var)
        ok = (len(p) == 312
              and p[:5] == HEADER and p[5:8] == STR_TYPE
              and p[dev_off:dev_off + 16] == dev.encode()
              and p[dev_off + 16:dev_off + 17] == b"-"
              and p[ts_off:ts_off + 10] == ts.encode()
              and p[ts_off + 10:ts_off + 15] == BIN_50_80
              and bytes([0x71, var]) in p
              and p[-11:] == TAIL
              and p.count(SIGNATURE) == 2)
        check(ok, f"binary payload structure #{i}", f"(len {len(p)}, sig x{p.count(SIGNATURE)})")
        if i == 0:
            check(pdd_base64_encode(p) != pdd_base64_encode(
                build_binary_payload("9999999999999999", ts, var)),
                "payload device_id sensitivity", "(device_id 参与格式)")

    # 3. zlib 层: level 9 -> 260~275B (随输入内容浮动) + 78 DA 头 + roundtrip
    p = build_binary_payload("1234567890123456", "1787156125", 0x7E)
    c = zlib.compress(p, 9)
    check(c[:2] == b"\x78\xda" and 260 <= len(c) <= 275,
          "zlib layer", f"({len(c)}B, header {c[:2].hex()})")
    check(zlib.decompress(c) == p, "zlib roundtrip", "")

    # 4. base64url 层: 无 +/= 字符 + roundtrip (长度 = ceil(压缩字节*4/3))
    enc = pdd_base64_encode(c)
    check(len(enc) == (len(c) * 4 + 2) // 3 and all(ch not in "+/=" for ch in enc),
          "base64url layer", f"({len(enc)} chars, no +/=)")
    check(pdd_base64_decode(enc) == c, "base64url roundtrip", "")

    # 5. 密钥流三元组 (2026-06-07 插桩): pt ^ ks == ct 且 ct ^ ks == pt
    for pt, ct, ks in KEYSTREAM_CASES:
        b_pt, b_ct, b_ks = (bytes.fromhex(x) for x in (pt, ct, ks))
        check(bytes(a ^ b for a, b in zip(b_pt, b_ks)) == b_ct
              and bytes(a ^ b for a, b in zip(b_ct, b_ks)) == b_pt,
              "keystream XOR self-verify",
              f"(zlib 78da... ^ ks = {b_ct.hex()})")

    # 6. 抓包前缀样例 (2026-06-07): 均以 0aq 开头 -> 密文头 D1 AA (文档截断, full=False)
    for s in AC_SAMPLES:
        ok, detail = check_anti_content_shape(s, full=False)
        check(ok, f"captured prefix {s[:12]}...", detail)

    # 7. Node 补环境全链路 (--node)
    if "--node" in sys.argv:
        a1 = generate_node()
        ok, d1 = check_anti_content_shape(a1)
        check(ok, "node generator run #1", d1)
        a2 = generate_node()
        ok, d2 = check_anti_content_shape(a2)
        check(ok, "node generator run #2", d2)
        check(a1 != a2, "node generator non-determinism",
              "(device_id/timestamp 每次随机)")
    else:
        print("[SKIP] --node full-chain (add --node, needs node)")

    # 8. 真实请求 (--live, 隐含 --node)
    if "--live" in sys.argv:
        ac = generate_node()
        status, success, count, name = live_request(ac)
        check(status == 200 and success and count > 0,
              "live API request",
              f"(HTTP {status}, success={success}, {count} goods: {name[:20]}...)")
    else:
        print("[SKIP] --live real request (add --live, needs network)")

    print(f"\n{passed}/{total} passed")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
