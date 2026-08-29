"""
pro29 公安部统计上报编码链 — encode64 / t / u / a 编码函数复现

复现 www.mps.gov.cn 站内搜索统计系统的参数编码链 (search_gxb.js 原版函数):

    encode64(input)  — 自实现 Base64, 与标准字符集一致 (仅 ASCII 输入与
                       Python base64.b64encode 完全兼容; 中文输入被 JS 的
                       charCodeAt 16 位截断语义破坏, 不在复现范围)
    t(text)          — 去 HTML 标签 + encodeURIComponent
    u(text)          — encodeURIComponent( encodeURIComponent( encode64(text) ) )
    a(obj)           — encodeURIComponent( encodeURIComponent( JSON.stringify(obj) ) )

用途: 统计上报通过 1×1 像素 Image Beacon 发送, 参数经上述编码链双层 URL 编码。
纯标准库, 无网络依赖。JS→Python 关键差异:
    - encodeURIComponent 不编码 A-Za-z0-9 - _ . ! ~ * ' ( )
      → urllib.parse.quote(s, safe="-_.!~*'()")
    - JSON.stringify == json.dumps(ensure_ascii=True, separators=(",", ":"))

用法:
    python main.py            # 5 组样例 (原站 JS 实测输出) 逐组对照

样例来源: 2026-06 mps.gov.cn 站内搜索 search_gxb.js 原函数实测
(原项目: spider research/其他/pro16 公安部/)
"""

import base64
import json
import re
from urllib.parse import quote

# JS encodeURIComponent 的安全字符集 (不编码的字符)
_SAFE = "-_.!~*'()"


# ---------------------------------------------------------------- 核心复现
def encode64(text: str) -> str:
    """复现 JS encode64(input) — 自实现标准 Base64。

    注意: 仅对 ASCII 输入与 Python base64.b64encode 一致。
    原版 JS 用 charCodeAt 逐字符取 16 位 code unit, 对中文 (>0xFF) 产生
    截断垃圾输出 (charAt 越界), 本实现不模拟该缺陷路径。
    """
    return base64.b64encode(text.encode("ascii")).decode("ascii")


def js_t(text: str) -> str:
    """复现 JS function t(t) — 去 HTML 标签 + encodeURIComponent。"""
    stripped = re.sub(r"<[^<>]+>", "", text)
    return quote(stripped, safe=_SAFE)


def js_u(text: str) -> str:
    """复现 JS function u(u) — encode64 后双层 encodeURIComponent。"""
    return quote(quote(encode64(text), safe=_SAFE), safe=_SAFE)


def js_a(obj) -> str:
    """复现 JS function a(a) — JSON.stringify 后双层 encodeURIComponent。

    JS JSON.stringify 不转义非 ASCII 字符 (直接输出 UTF-8 原字符),
    对应 Python json.dumps(ensure_ascii=False)。
    """
    body = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    return quote(quote(body, safe=_SAFE), safe=_SAFE)


# ---------------------------------------------------------------- 样例验证
# (函数名, 输入, 期望输出) — 5 组取自原站 search_gxb.js 函数实测 (2026-06)
SAMPLE_CASES = [
    ("encode64", "hello world", "aGVsbG8gd29ybGQ="),
    ("encode64", "abc", "YWJj"),
    ("t", "<p>公安部</p>通知", "%E5%85%AC%E5%AE%89%E9%83%A8%E9%80%9A%E7%9F%A5"),
    ("u", "test/123", "dGVzdC8xMjM%253D"),
    ("a", {"name": "公安部", "id": 123, "list": [1, 2]},
     "%257B%2522name%2522%253A%2522%25E5%2585%25AC%25E5%25AE%2589%25E9%2583%25A8"
     "%2522%252C%2522id%2522%253A123%252C%2522list%2522%253A%255B1%252C2%255D%257D"),
]

_FUNCS = {"encode64": encode64, "t": js_t, "u": js_u, "a": js_a}


def main() -> None:
    passed = 0
    for name, inp, expected in SAMPLE_CASES:
        got = _FUNCS[name](inp)
        ok = got == expected
        passed += ok
        print("[%s] %s(%s)" % ("PASS" if ok else "FAIL", name, repr(inp)[:40]))
        print("      got     : %s" % got[:90])
        if not ok:
            print("      expected: %s" % expected[:90])
    print("\n%d/%d 通过" % (passed, len(SAMPLE_CASES)))
    if passed != len(SAMPLE_CASES):
        raise SystemExit(1)


# ---------------------------------------------------------------- 可选: AST 教学 demo
# ast_deobfuscate_demo.js — Babel AST 反混淆教学演示 (自带样例, node 直接跑):
#   node ast_deobfuscate_demo.js
# 演示内容: 字符串数组还原 / 索引访问替换 / 常量折叠, 见同目录 AST教学指南.md

if __name__ == "__main__":
    main()
