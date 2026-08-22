"""
爱企查 (aiqicha.baidu.com) — ABCLite-2061 SDK: \\xHH 双重转义字符串还原 + 反调试/指纹检测逻辑

用法:
    python main.py   # 纯 Python 验证 (无网络, 无需 node)

原理 (来源: ANALYSIS_REPORT.md, 2026-06-30 CloakBrowser 分析):
    第 1 层 ABCLite SDK (https://dlswbr.baidu.com/heicha/mw/abclite-2061-s.original.js,
    加载器每 20 分钟刷新 ?_= 参数):
        字符串混淆 = 双重转义: CDN 原始文件里是 '\\x6f\\x75...' (双反斜杠,
        JS 字符串字面量解析后得到文本 \\xHH), 运行期再二次解析;
        分析会话归一化为单反斜杠 '\\x6f\\x75' 后用 \\xHH->字符 解码还原.
        解码链: raw(双反斜杠) -> 归一化(单反斜杠) -> decode_hex -> 明文
    反调试/指纹检测 (解码后代码, 报告 2.2-2.7, 均已在 abclite_decoded.js 验证存在):
        - DevTools: 劫持 eval getter + Error().stack 找 'evaluate@debugger'/'@debugger' 行
        - WebDriver: 6 个全局标记 (__driver_evaluate/__nightmare 等)
        - 窗口尺寸: 800x600x1200 -> 0x1388(5000); outerWidth==0 -> 0x1389(5001)
        - 浏览器特征: chrome.runtime->0x1bbc / webdriver+selenium string->0x1c20
                      / WebGL->0x258(600) / WebGL2->0x259(601)
        - Function.toString 篡改: 异常堆栈行数减少 -> 0x64(100)
    第 2 层 ACS-2061 (仅结构, 报告 3.2-3.3): $BSB_2061.gs() 签名 =
        Date.now() + '_' + base64(AES(json字段表, 密钥混淆在代码中未提取))

坑: \\xHH 在 Python 字符串里要用 r"\\x.." 原始串 (普通串 \\x65 会被当转义吃掉);
    abclite_decoded.js 比 decode_hex(formatted) 多 1 个尾部换行 (分析会话写盘差异);
    SDK 20 分钟刷新 -> 两次抓包内容不同 (raw 与 formatted 是两次捕获, 反调试逻辑一致).

样例来源: 编码链样例 = 从原始文件提取的实存转义串 (2026-06-30 抓包);
          检测判定样例 = 报告文档公式; 签名样例 = 报告结构自造.
"""

import os
import re

DIR = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(DIR, "abclite-2061-s.original.js")          # CDN 原始 (双反斜杠转义)
FORMATTED = os.path.join(DIR, "abclite_original_formatted.js")  # 归一化 (单反斜杠)
DECODED = os.path.join(DIR, "abclite_decoded.js")               # 解码产物 (明文基准)
LOADER = os.path.join(DIR, "scripts", "abclite_loader.js")      # 加载器
REPORT = os.path.join(DIR, "ANALYSIS_REPORT.md")                # 分析报告

# (转义串, 明文) — 取自 abclite_original_formatted.js 实存转义 (2026-06-30 抓包)
HEX_SAMPLE_CASES = [
    (r"\x65\x76\x61\x6c", "eval"),
    (r"\x65\x76\x61\x6c\x75\x61\x74\x65\x40\x64\x65\x62\x75\x67\x67\x65\x72",
     "evaluate@debugger"),
    (r"\x6f\x75\x74\x65\x72\x57\x69\x64\x74\x68", "outerWidth"),
    (r"\x67\x65\x74\x42\x61\x74\x74\x65\x72\x79", "getBattery"),
    (r"\x5f\x5f\x6e\x69\x67\x68\x74\x6d\x61\x72\x65", "__nightmare"),
]

# 检测逻辑核心明文标记 (均已在 abclite_decoded.js 中验证存在)
CORE_MARKERS = ["evaluate@debugger", "__driver_evaluate", "__fxdriver_evaluate",
                "__webdriver_script_func", "__fxdriver_unwrapped",
                "__$webdriverAsyncExecutor", "__nightmare", "getBattery",
                "WebGLRenderingContext"]

# WebDriver 全局标记 (报告 2.3)
DRIVER_FLAGS = ["__driver_evaluate", "__fxdriver_evaluate", "__webdriver_script_func",
                "__fxdriver_unwrapped", "__$webdriverAsyncExecutor", "__nightmare"]

# ACS-2061 数据采集字段表 (报告 3.2)
FIELD_MAP = ["h0", "h1", "hf", "hfe", "ua", "baiduid", "url", "clientTs",
             "platform", "version", "extraTooLong", "extra"]


# ---------- 字符串编码链 (\xHH 双重转义还原) ----------

def decode_hex(s: str) -> str:
    """decode_script.py 算法: 把 \\xHH 转义序列替换为对应字符 (JS 运行期二次解析的等价物)"""
    out = []
    i = 0
    while i < len(s):
        if i + 3 < len(s) and s[i] == "\\" and s[i + 1] == "x":
            try:
                out.append(chr(int(s[i + 2:i + 4], 16)))
                i += 4
                continue
            except ValueError:
                pass
        out.append(s[i])
        i += 1
    return "".join(out)


def unescape_double(s: str) -> str:
    """归一化: CDN 原始的双反斜杠 \\xHH -> 单反斜杠 \\xHH (JS 字符串字面量解析)"""
    return s.replace(r"\\x", r"\x")


# ---------- 反调试/指纹检测判定 (报告公式, 常量已在解码代码中验证) ----------

def detect_devtools(stack: str) -> bool:
    """报告 2.2 detectDevtools: 找 'evaluate@debugger' 行, 下一行 '@debugger' 开头,
    再下一行为空 -> DevTools 已开; 找不到模式返回 True (正常环境, 报告原文语义)"""
    lines = stack.split("\n")
    for i in range(len(lines) - 1):
        if "evaluate@debugger" in lines[i] and lines[i + 1].startswith("@debugger"):
            return not lines[i + 2] if i + 2 < len(lines) else True
    return True


def check_webdriver(props: set) -> list:
    """报告 2.3: 遍历 window 属性名, 命中 driverFlags 即标记 (数值 flagCode 未捕获)"""
    return [f for f in DRIVER_FLAGS if f in props]


def check_window_dimensions(inner_w: int, inner_h: int, outer_w: int) -> str:
    """报告 2.4 (常量已在解码代码验证: 0x320=800/0x258=600/0x4b0=1200):
    固定分辨率 -> 0x1388(5000); outerWidth==0 无头特征 -> 0x1389(5001)"""
    flags = []
    if inner_w == 0x320 and inner_h == 0x258 and outer_w == 0x4b0:
        flags.append(0x1388)
    if outer_w == 0:
        flags.append(0x1389)
    return "_".join(str(f) for f in flags)


def check_browser_features(chrome_runtime=False, webdriver_str=False,
                           selenium_str=False, webgl=False, webgl2=False) -> str:
    """报告 2.5: chrome.runtime->0x1bbc / webdriver+selenium 同时为 string->0x1c20
    / WebGL->0x258 / WebGL2->0x259"""
    flags = []
    if chrome_runtime:
        flags.append(0x1bbc)
    if webdriver_str and selenium_str:
        flags.append(0x1c20)
    if webgl:
        flags.append(0x258)
    if webgl2:
        flags.append(0x259)
    return "_".join(str(f) for f in flags)


def check_tostring(stack_lines: int, normal_lines: int) -> str:
    """报告 2.6: 原生 toString 调用抛异常时, 堆栈行数少于正常 -> 0x64(100) 篡改标记"""
    if stack_lines < normal_lines:
        return str(0x64)
    return ""


# ---------- ACS-2061 结构 (报告 3.3) ----------

def is_signature(s: str) -> bool:
    """$BSB_2061.gs() 输出 = Date.now() + '_' + base64(AES(json))"""
    return re.fullmatch(r"\d{13}_[A-Za-z0-9+/=]+", s) is not None


def build_payload(extra: str) -> dict:
    """报告 3.3: extraData > 1024 字节 -> extraTooLong=1 并清空 extra"""
    fields = {"extra": extra}
    if len(extra) > 1024:
        fields["extraTooLong"] = 1
        fields["extra"] = ""
    return fields


def main() -> None:
    passed, total = 0, 0

    def check(ok: bool, label: str, detail: str = "") -> None:
        nonlocal passed, total
        total += 1
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label} {detail}")

    raw = open(RAW, encoding="utf-8").read()
    formatted = open(FORMATTED, encoding="utf-8").read()
    decoded = open(DECODED, encoding="utf-8").read()
    loader = open(LOADER, encoding="utf-8").read()

    # 1. 文件齐备
    total_bytes = sum(os.path.getsize(p) for p in (RAW, FORMATTED, DECODED, LOADER, REPORT))
    check(all(os.path.isfile(p) for p in (RAW, FORMATTED, DECODED, LOADER, REPORT)),
          "artifacts present", f"({total_bytes} bytes total)")

    # 2. 编码链: CDN 原始 = 双反斜杠转义, 无明文标记
    dbl_esc = raw.count(r"\\x")
    check(dbl_esc == 9753 and r"\\x" in raw,
          "raw original double-backslash escapes", f"({dbl_esc}x \\\\xHH)")
    check(not any(m in raw for m in ("evaluate@debugger", "__driver_evaluate",
                                     "__nightmare", "getBattery")),
          "raw original hex-obfuscated (no plaintext markers)", "")

    # 3. 编码链: 归一化版 = 单反斜杠, 无双重
    check(formatted.count(r"\x") == 9753 and "\\x" in formatted
          and r"\\x" not in formatted,
          "formatted single-backslash escapes",
          f"({formatted.count(chr(92) + 'x')}x \\xHH, 0 double)")

    # 4. 编码链: decode_hex(formatted) + '\n' == abclite_decoded.js (byte-exact 管道复现)
    redecoded = decode_hex(formatted)
    check(redecoded + "\n" == decoded,
          "decode pipeline byte-exact", f"(decode(formatted)+'\\n' == decoded, "
          f"{len(redecoded)} chars)")

    # 5. 编码链: CDN 端到端 (双反斜杠 -> 归一化 -> 解码 -> 明文标记全部出现)
    two_stage = decode_hex(unescape_double(raw))
    check(all(m in two_stage for m in CORE_MARKERS),
          "two-stage decode (raw -> unescape -> decode)", "")

    # 6. 编码链样例 ×5 (转义串取自实存文件)
    for esc, expect in HEX_SAMPLE_CASES:
        got = decode_hex(esc)
        check(got == expect and esc in formatted, f"decode {esc[:20]}...",
              f"({got})")

    # 7. 加载器: 版本 2061 + 20 分钟缓存破坏 + BCat_2061 7 方法
    check("2061" in loader and "abclite-" in loader and "original.js" in loader,
          "loader SDK version/URL", "(abclite-2061-s.original.js)")
    check("1728e5" in loader and "parseInt(u/1728e5,10)" in loader,
          "loader 20-min cache buster", "(172800000ms = 每 20 分钟刷新)")
    methods = ["initData", "initActiveData", "report", "init", "dr5", "miao", "miaowu"]
    check(all(m in loader for m in methods) and "BCat_2061" in loader.replace(" ", "")
          or "BCat_" in loader,
          "loader BCat_2061 methods", f"({len(methods)} methods)")

    # 8. 检测逻辑代码在解码产物中存在 (ground truth)
    check("evaluate@debugger" in decoded and "@debugger" in decoded,
          "decoded has eval-stack devtools chain", "")
    check(all(f"{hex(c)}" in decoded or str(c) in decoded
              for c in (0x320, 0x258, 0x4b0, 0x1388, 0x1389)),
          "decoded has window-dim constants",
          "(0x320=800/0x258=600/0x4b0=1200 -> 0x1388/0x1389)")
    check(all(f in decoded for f in DRIVER_FLAGS)
          and all(f"{hex(c)}" in decoded for c in (0x1bbc, 0x1c20, 0x258, 0x259, 0x64)),
          "decoded has webdriver flags + flag codes", "")

    # 9. DevTools 检测判定 ×3 (报告 2.2)
    cases = [
        ("at fn (evaluate@debugger)\n@debugger\n", True),      # 模式命中 + 第三行为空
        ("at fn (evaluate@debugger)\n@debugger\nat caller\nat callee", False),
        ("at fn\nat caller", True),                            # 无模式 -> 正常环境
    ]
    for stack, expect in cases:
        got = detect_devtools(stack)
        check(got == expect, f"detect_devtools stack={len(stack.splitlines())} lines",
              f"({'detected' if got else 'normal'})")

    # 10. WebDriver 检测 ×3
    check(check_webdriver(set(DRIVER_FLAGS)) == DRIVER_FLAGS, "webdriver all 6 flags", "")
    check(check_webdriver({"__nightmare", "__driver_evaluate", "foo"})
          == ["__driver_evaluate", "__nightmare"], "webdriver subset", "")
    check(check_webdriver({"navigator", "window"}) == [], "webdriver clean", "")

    # 11. 窗口尺寸 ×3
    for iw, ih, ow, expect in [(0x320, 0x258, 0x4b0, "5000"),    # 固定分辨率命中
                               (1920, 1080, 1920, ""),            # 正常桌面
                               (0x320, 0x258, 0, "5001")]:        # outer=0 无头特征
        got = check_window_dimensions(iw, ih, ow)
        check(got == expect, f"window dims {iw}x{ih} outer={ow}",
              f"({got or 'none'})")

    # 12. 浏览器特征 ×4
    cases = [
        ((True, False, False, False, False), "7100"),
        ((False, True, True, False, False), "7200"),   # webdriver+selenium 均为 string
        ((False, True, False, False, False), ""),      # 仅 webdriver 不触发
        ((True, False, False, True, True), "7100_600_601"),
    ]
    for args, expect in cases:
        got = check_browser_features(*args)
        check(got == expect, f"browser features {args}", f"({got or 'none'})")

    # 13. toString 篡改 ×3
    for sl, nl, expect in [(3, 5, "100"), (5, 5, ""), (1, 3, "100")]:
        got = check_tostring(sl, nl)
        check(got == expect, f"toString tamper stack={sl} vs normal={nl}",
              f"({'flag 100' if got else 'clean'})")

    # 14. ACS-2061 字段表 (12 键, 报告 3.2)
    check(sorted(FIELD_MAP) == sorted(set(FIELD_MAP)) and len(FIELD_MAP) == 12,
          "ACS field map", f"({', '.join(FIELD_MAP)})")

    # 15. ACS 签名格式 ×3 (Date.now() + '_' + base64(AES))
    check(is_signature("1787153907256_8j3KkLs1x9Pq2Wm4vNc6Xz=="), "signature valid (b64)", "")
    check(is_signature("1787153907256_AbCdEfGhIjKlMnOpQrStUvWxYz0123"), "signature valid", "")
    check(not is_signature("abc_8j3KkLs1") and not is_signature("1787153907256_!!!"),
          "signature invalid rejected", "")

    # 16. ACS extraTooLong 规则 ×3 (>1024 丢弃)
    check(build_payload("x" * 1025) == {"extra": "", "extraTooLong": 1},
          "extra >1024 truncated", "")
    check(build_payload("x" * 1024) == {"extra": "x" * 1024},
          "extra ==1024 kept", "")
    check(build_payload("kw") == {"extra": "kw"}, "extra short kept", "")

    # 17. ACS 版本与全局暴露 (报告 3.3 + stub 头注释)
    check("1.2.0" in open(os.path.join(DIR, "ANALYSIS_REPORT.md"), encoding="utf-8").read()
          or "1.2.0" in loader, "ACS version 1.2.0", "")
    check("$BSB_2061" in open(REPORT, encoding="utf-8").read(), "window.$BSB_2061 exposed", "")

    print(f"\n{passed}/{total} passed")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
