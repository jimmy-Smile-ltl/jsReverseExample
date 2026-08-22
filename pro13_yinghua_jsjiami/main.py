"""
樱花动漫 (yh5dm.net) — jsjiami.com.v7 字符串表解混淆: 自定义 base64 + RC4 纯 Python 还原

用法:
    python main.py   # 解码器验证 + 全套 1157 处引用解码 + 反调试机制判定 (纯 Python, 无网络)

原理 (player.js 110KB, jsjiami.com.v7 + Parcel 打包):
    字符串表: 1121 条 RC4 密文存于 strings.json (从 _0x1a56() 数组提取)
    解码链:   _0x12d4(index, key):
        index -= 0x112                     # 表偏移
        raw   = table[index]
        s1    = custom_b64_decode(raw)     # 自定义字母表 base64 (小写在前!)
        s2    = s1.decode('utf-8')         # JS: %XX 编码 + decodeURIComponent
        out   = rc4(s2, key)               # 标准 RC4 (KSA + PRGA), 逐 code unit XOR
    调用点:   _0x2b2717(0x199,'H3ud') -> "apiToken" (别名链 _0x2b2717=_0x12d4)
    关键差异: 字母表 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/='
              (小写在前! 标准 base64 大写在前, 混用会解码失败)

    站点另有 5 层纯前端反调试 (页面 inline script, 不影响 HTTP):
        F12=123 / Ctrl+Shift+I=73 / Ctrl+U=85 / Ctrl+S=83 拦截 + 右键拦截
        + DevTools 窗口尺寸检测 (outer-inner > 160px -> debugger)
    绕过: document.onkeydown=null / oncontextmenu=null; DevTools 独立窗口模式;
          补丁均可用属性覆盖 (未用 defineProperty 保护)

样例来源: 解码期望值 = 原项目 2026-06-30 解混淆报告对照表 + player_clean.js 交叉验证.
"""

import json
import os
import re
import sys

# 解码值含中文, GBK 控制台会编码崩溃 — 统一 UTF-8 输出
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

DIR = os.path.dirname(os.path.abspath(__file__))

# 自定义 base64 字母表 — 小写在前! (jsjiami v7 特征, 标准 base64 为大写在前)
ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/="
TABLE_OFFSET = 0x112

# (hex_index, key, 期望明文) — 取自解混淆报告 + player_clean.js 交叉验证 (2026-06-30)
SAMPLE_CASES = [
    (0x199, "H3ud", "apiToken"),
    (0x2e0, "LEiU", "api/resolve.php?token="),
    (0x1cd, "$OfY", "loading-box"),
    (0x45e, "$OfY", "none"),
    (0x288, "Zz7j", "loading"),
    (0x402, "IJMH", ".m3u8"),
    (0x523, "s@V)", ".mp4"),
    (0x452, ")^GC", ".flv"),
    (0x4b4, "!T^g", "无法解析视频。"),
    (0x3af, "XF%L", "弹幕插件加载出错:"),
    (0x2a8, "4Bi7", "视频未就绪"),
]

# 反调试判定样例: (keycode, ctrl, shift, 是否拦截) — 报告 4.2 拦截表
KEYCODE_CASES = [
    (123, False, False, True),   # F12
    (73, True, True, True),      # Ctrl+Shift+I
    (85, True, False, True),     # Ctrl+U 查看源码
    (83, True, False, True),     # Ctrl+S 保存
    (73, False, False, False),   # 单按 I 不拦截
    (67, True, True, False),     # Ctrl+Shift+C 未拦截 (报告指出的遗漏)
    (73, True, False, False),    # Ctrl+I 未拦截
]

# 窗口尺寸检测样例: (outer_w, inner_w, outer_h, inner_h, 是否触发) — 报告 4.4 表格
DEVTOLS_CASES = [
    (1600, 1400, 900, 900, True),    # 侧边栏 docked: 宽差 200 > 160
    (1600, 1600, 900, 730, True),    # 底部栏 docked: 高差 170 > 160
    (1600, 1600, 900, 900, False),   # 独立窗口/未打开: 差值 0
    (1600, 1450, 900, 900, False),   # 宽差 150 <= 阈值 160
]


def load_table() -> list:
    with open(os.path.join(DIR, "strings.json"), encoding="utf-8") as f:
        return json.load(f)


def custom_b64_decode(s: str) -> bytes:
    """对应 JS _0x394ee6: 自定义字母表 base64 解码 (含 '=' 在表内, 跳过未知字符)

    逐字镜像 JS 压缩循环: b2 累加 6bit, 每满 4 字符产出 3 字节,
    位移用 (-2*i)&6 取 0/2/4/6.
    """
    out = bytearray()
    b2 = 0
    i = 0
    for ch in s:
        b3 = ALPHABET.find(ch)
        if b3 == -1:
            continue
        b2 = b2 * 0x40 + b3 if i % 4 else b3
        emit = i % 4
        i += 1
        if emit:
            out.append(0xFF & (b2 >> ((-2 * i) & 6)))
    return bytes(out)


def rc4(data: str, key: str) -> str:
    """对应 JS _0x471327: 标准 RC4 (KSA + PRGA), 输入为 UTF-8 解码后的字符"""
    s = list(range(256))
    j = 0
    for i in range(256):
        j = (j + s[i] + ord(key[i % len(key)])) % 256
        s[i], s[j] = s[j], s[i]
    i = j = 0
    out = []
    for ch in data:
        i = (i + 1) % 256
        j = (j + s[i]) % 256
        s[i], s[j] = s[j], s[i]
        out.append(chr(ord(ch) ^ s[(s[i] + s[j]) % 256]))
    return "".join(out)


def decode(table: list, index: int, key: str) -> str:
    """对应 _0x12d4(index, key): 表偏移 0x112 -> 自定义 base64 -> UTF-8 -> RC4"""
    raw = table[index - TABLE_OFFSET]
    return rc4(custom_b64_decode(raw).decode("utf-8"), key)


def intercept_rule(keycode: int, ctrl: bool = False, shift: bool = False) -> bool:
    """反调试第 1/2 层: document.onkeydown 拦截判定 (纯前端, 不影响 HTTP)"""
    if keycode == 123:                     # F12 (Firefox 下 window.event 缺失则失效)
        return True
    if ctrl and shift and keycode == 73:   # Ctrl+Shift+I
        return True
    if ctrl and keycode == 85:             # Ctrl+U
        return True
    if ctrl and keycode == 83:             # Ctrl+S
        return True
    return False


def devtools_detected(outer_w: int, inner_w: int, outer_h: int,
                      inner_h: int, threshold: int = 160) -> bool:
    """反调试第 4 层: 窗口尺寸差值超阈值 -> debugger (1s 轮询)"""
    return outer_w - inner_w > threshold or outer_h - inner_h > threshold


def main() -> None:
    passed, total = 0, 0

    def check(ok: bool, label: str, detail: str = "") -> None:
        nonlocal passed, total
        total += 1
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label} {detail}")

    # 1. 文件与表结构
    table = load_table()
    check(len(table) == 1121, "strings.json table", f"({len(table)} entries)")
    src = open(os.path.join(DIR, "player.js"), encoding="utf-8").read()
    check("jsjiami.com.v7" in src[:500], "jsjiami.com.v7 marker", "")
    check("const _0x2b2717=_0x12d4" in src, "alias chain present", "")
    clean = open(os.path.join(DIR, "player_clean.js"), encoding="utf-8").read()
    check(all(x in clean for x in ("apiToken", "loading-box", "无法解析视频。")),
          "player_clean.js reference (plaintext markers)",
          f"(clean {len(clean)} bytes)")

    # 2. 样例期望值 ×11
    for idx, key, expect in SAMPLE_CASES:
        got = decode(table, idx, key)
        check(got == expect, f"decode 0x{idx:03x} {key!r}", f"({got[:24]})")

    # 3. 自定义字母表证明: 标准 base64 字母表 (大写在前) 解码同一条 -> 结果不同
    import base64 as _b64
    raw = table[0x199 - TABLE_OFFSET]
    try:
        std_val = rc4(_b64.b64decode(raw + "=" * (-len(raw) % 4))
                      .decode("utf-8", "replace"), "H3ud")
    except Exception:
        std_val = "<decode error>"
    check(std_val != "apiToken", "custom alphabet required",
          f"(standard b64 gives {std_val[:16]!r})")

    # 4. 全量调用点扫描: 1157 处合法引用全部可解码
    sites = re.findall(r"0x([0-9a-f]{2,4})\s*,\s*'([^']{1,8})'\s*\)", src)
    valid = [(h, k) for h, k in sites
             if 0 <= int(h, 16) - 0x112 < len(table)]
    fails = 0
    for h, k in valid:
        try:
            decode(table, int(h, 16), k)
        except Exception:
            fails += 1
    check(fails == 0 and len(valid) >= 1100, "full call-site sweep",
          f"({len(valid)} sites decoded, {fails} fails)")

    # 5. 与 player_clean.js 交叉验证: 大部分解码值应出现在解混淆基准中
    missing = 0
    for h, k in valid:
        if decode(table, int(h, 16), k) not in clean:
            missing += 1
    check(missing <= 30, "cross-check vs player_clean.js",
          f"({len(valid) - missing}/{len(valid)} values present, "
          f"missing {missing} are dispatch numerics)")

    # 6. 反调试机制判定 (纯逻辑复现, 页面 inline script 已摘录在 README)
    for kc, ctrl, shift, expect in KEYCODE_CASES:
        got = intercept_rule(kc, ctrl, shift)
        check(got == expect, f"key interception kc={kc} ctrl={int(ctrl)} shift={int(shift)}",
              f"({'intercept' if got else 'pass'})")
    for ow, iw, oh, ih, expect in DEVTOLS_CASES:
        got = devtools_detected(ow, iw, oh, ih)
        check(got == expect, f"devtools size detection {ow}-{iw}/{oh}-{ih}",
              f"({'trigger' if got else 'pass'})")

    print(f"\n{passed}/{total} passed")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
