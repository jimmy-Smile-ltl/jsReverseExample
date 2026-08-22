"""
pro26 南方航空 — 搜索请求参数关系复现（encryptArgs 绕过方案的确定性部分）

站点使用 AWS CloudFront WAF + RSA+RC4 加密 + encryptArgs 令牌机制,
原项目未做 crypto 逆向, 而是通过隐身浏览器 (Playwright+stealth) 直接
在真实页面执行搜索, 再从 Vuex store 提取 `state.execution.info` 拿到
合法参数。本文件复现抓包数据中可确定性验证的请求参数关系:

    searchParams.execution = 32 位 hex 令牌 (服务端派生, 算法未逆向)
    requestId = base64url("sliceGrid:B2C_SEARCH_{dep}-{arr}_{date}_{execution}")

用法:
    python main.py            # 运行 3 组内置抓包样例, 输出即验证

抓包来源: 2026-06, https://global.csair.com 机票搜索 (auto_version/test_*.json)
"""

import base64
import json

# ---------------------------------------------------------------- 核心复现
def build_request_id(dep: str, arr: str, date: str, execution: str) -> str:
    """JS→Python 对照: 前端 sliceGrid 构造的 requestId (base64url, 无 padding)。

    JS: btoa("sliceGrid:B2C_SEARCH_" + dep + "-" + arr + "_" + date + "_" + execution)
    差异: JS btoa 对 UTF-8 串直接按字节编码, 与 Python base64.b64encode 一致;
          URL 传递时去 '=' padding。
    """
    raw = "sliceGrid:B2C_SEARCH_%s-%s_%s_%s" % (dep, arr, date, execution)
    return base64.b64encode(raw.encode("utf-8")).decode("utf-8").rstrip("=")


def parse_request_id(request_id: str) -> dict:
    """解码 requestId, 提取 execution 令牌与航线信息 (验证用)。

    格式: sliceGrid:B2C_SEARCH_{dep}-{arr}_{date}_{execution}
    (前缀本身含两个下划线, 故从右向左拆)
    """
    pad = request_id + "=" * (-len(request_id) % 4)
    raw = base64.b64decode(pad).decode("utf-8")
    seg = raw.rsplit("_", 2)            # ["sliceGrid:B2C_SEARCH_LAX-CAN", "2026-06-10", "xxx"]
    execution = seg[2]
    date = seg[1]
    dep, arr = seg[0].rsplit("_", 1)[1].split("-")
    return {"prefix": "sliceGrid:B2C_SEARCH", "dep": dep, "arr": arr, "date": date, "execution": execution}


# ---------------------------------------------------------------- 样例验证
# (dep, arr, date, execution, 期望 requestId) — 取自 2026-06 抓包
SAMPLE_CASES = [
    ("LAX", "CAN", "2026-06-10", "78080ec6638543b881b9d2ade2ed8245",
     "c2xpY2VHcmlkOkIyQ19TRUFSQ0hfTEFYLUNBTl8yMDI2LTA2LTEwXzc4MDgwZWM2NjM4NTQzYjg4MWI5ZDJhZGUyZWQ4MjQ1"),  # test_oneway.json
    ("LAX", "CAN", "2026-06-10", "9c8ed616cae6f44483e77888b5db3907",
     "c2xpY2VHcmlkOkIyQ19TRUFSQ0hfTEFYLUNBTl8yMDI2LTA2LTEwXzljOGVkNjE2Y2FlNmY0NDQ4M2U3Nzg4OGI1ZGIzOTA3"),  # test_round.json (第一段)
    ("LAX", "CAN", "2026-06-10", "3886d69ef769b7313184e27150a44207",
     "c2xpY2VHcmlkOkIyQ19TRUFSQ0hfTEFYLUNBTl8yMDI2LTA2LTEwXzM4ODZkNjllZjc2OWI3MzEzMTg0ZTI3MTUwYTQ0MjA3"),  # test_round2.json (第一段)
]


def main() -> None:
    print("capture           execution                       requestId 校验")
    passed = 0
    for dep, arr, date, execution, expected in SAMPLE_CASES:
        got = build_request_id(dep, arr, date, execution)
        ok = got == expected
        passed += ok
        print("%-17s %-32s %s" % ("%s-%s %s" % (dep, arr, date), execution, "PASS" if ok else "FAIL"))
        if not ok:
            print("      expected: " + expected)
            print("      got     : " + got)
    # 反向解析验证: execution 能从 requestId 复原
    for dep, arr, date, execution, expected in SAMPLE_CASES:
        parsed = parse_request_id(expected)
        assert parsed["execution"] == execution and parsed["dep"] == dep, parsed
    print()
    print("反向解析: 3 组 requestId 均能复原 execution/航线/日期")
    print()
    print("%d/%d 通过" % (passed, len(SAMPLE_CASES)))
    if passed != len(SAMPLE_CASES):
        raise SystemExit(1)


# ---------------------------------------------------------------- 可选: 真实请求验证
# 加密链路 (RSA+RC4 / encryptArgs 令牌) 未逆向: 原项目通过隐身浏览器 +
# Vuex store 提取 state.execution.info 绕过, 见 README「逆向摘要」。
# 如需复现加密本身, 需逆向 /api/shop/app 的请求体加密与 /api/shop/decryptArgs。

if __name__ == "__main__":
    main()
