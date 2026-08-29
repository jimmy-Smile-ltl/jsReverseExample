"""
pro31 天辰文学 (tcl2024.com) JS 内容加密 — 章节响应判别与还原骨架

反爬机制: 章节 URL 返回的不是 HTML 而是可执行 JS 代码, 执行后才产生正文。
原项目 (无限集数/小说/山沟皇帝_tcl2024.ipynb) 流程:

    GET /files/article/html555/0/768/{id}.html
    → 响应体是 JS (密文, 形如 document.write(...) / 字符串拼接)
    → js2py.eval_js(txt) 执行还原 → 正文 → &nbsp; 清洗 + <br> 换行

⚠️ 站点已死亡 (2026-08 实测 CDN 节点无响应), 真实密文样例已不可获取,
    解码算法无法还原。本文件提供两个可离线验证的确定性环节:
    1) 章节响应判别器: JS 密文 vs 明文 HTML
    2) 还原执行骨架: node 执行 JS 密文产出正文 (替代不兼容 Py3.12 的 js2py)

用法:
    python main.py            # 演示用例判别 + node 还原流程验证

依赖: node (v16+); Python 仅标准库。
样例说明: 下方 3 组为「机制演示用例」(自造 JS 密文形态), 非真实抓包
          —— 真实密文随站点死亡已不可得, 请勿将其当作抓包样例引用。
"""

import os
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EVAL_JS = os.path.join(BASE_DIR, "eval_chapter.js")

# ---------------------------------------------------------------- 核心复现
def classify_chapter(raw: str) -> str:
    """判别章节响应类型 (对齐原 notebook 隐式流程: 直接 eval 成功 = JS 密文)。

    返回 "js_cipher" | "html_plain" | "unknown":
    - js_cipher: 以 JS 语句/变量声明开头, 或以 document./window./var/let/const
      起始的可执行代码 (站点密文形态)
    - html_plain: 以 < 开头或含 <html/<div 等标签 (普通站点正文)
    """
    head = raw.lstrip()[:200].lower()
    if head.startswith("<") or "<html" in head or "<div" in head or "<!doctype" in head:
        return "html_plain"
    if head.startswith(("document.", "window.", "var ", "let ", "const ", "function ")):
        return "js_cipher"
    if head.startswith("eval(") or head.startswith("("):
        return "js_cipher"
    return "unknown"


def eval_chapter_js(code: str) -> str:
    """用 node 执行 JS 密文, 返回还原后的正文 (对齐 js2py.eval_js 语义)。"""
    result = subprocess.run(
        ["node", EVAL_JS, code],
        capture_output=True, text=True, timeout=30, cwd=BASE_DIR,
        encoding="utf-8", errors="replace",  # node 输出为 UTF-8, 勿用 GBK 默认
    )
    if result.returncode != 0:
        raise RuntimeError("node 执行失败: %s" % result.stderr[-300:])
    return result.stdout


def decode_chapter(raw: str) -> str:
    """完整还原流程: 判别 → (JS 密文则 node 执行) → 清洗 &nbsp; 与 <br>。"""
    kind = classify_chapter(raw)
    if kind == "js_cipher":
        text = eval_chapter_js(raw)
    else:
        text = raw
    return (text.replace("&nbsp;", " ")
            .replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n"))


# ---------------------------------------------------------------- 样例验证
# (输入, 期望类型, 期望正文) — 机制演示用例 (自造形态, 非真实抓包)
SAMPLE_CASES = [
    # 站点典型密文形态: document.write 输出正文
    ('document.write("第1章 山沟皇帝\\n<br>皇恩浩荡。");',
     "js_cipher",
     "第1章 山沟皇帝\n\n皇恩浩荡。\n"),
    # 字符串拼接形态 (小说站常见): 变量拼接后 write
    ('var a="第一回";var b=" 山沟";document.write(a+b+"\\n<br>完");',
     "js_cipher",
     "第一回 山沟\n\n完\n"),
    # 明文 HTML 形态: 判别器应放行不执行
    ('<html><body><div id="txt">第1章 正文内容</div></body></html>',
     "html_plain",
     "<html><body><div id=\"txt\">第1章 正文内容</div></body></html>"),
]


def main() -> None:
    passed = 0
    for raw, kind, expected in SAMPLE_CASES:
        try:
            got_kind = classify_chapter(raw)
            got = decode_chapter(raw)
            ok = got_kind == kind and got.strip() == expected.strip()
            passed += ok
            print("[%s] 类型=%s" % ("PASS" if ok else "FAIL", got_kind))
            print("      还原: %s" % got.replace("\n", " / ")[:80])
            if not ok:
                print("      期望类型: %s  期望: %s" % (kind, expected.replace("\n", " / ")[:80]))
        except Exception as e:
            print("[FAIL] 异常: %s" % e)
    print("\n%d/%d 通过" % (passed, len(SAMPLE_CASES)))
    if passed != len(SAMPLE_CASES):
        raise SystemExit(1)


# ---------------------------------------------------------------- 可选: 真实请求验证
# 站点已死亡 (2026-08-22 实测: DNS 在但 CDN 节点 23.224.4.115 无响应,
# 镜像域名全挂)。原 notebook 真实流程 (2024-06):
#   GET https://www.tcl2024.com/files/article/html555/0/768/{id}.html
#   → js2py.eval_js(txt) → re.sub("&nbsp;","") + <br> 换行 → 存 txt
# 如站点复活, 抓一章存密文即可补全 SAMPLE_CASES 并还原解码算法。

if __name__ == "__main__":
    main()
