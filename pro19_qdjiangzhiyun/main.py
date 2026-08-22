"""
qdjiangzhiyun 小说站 — 章节正文解码: Base64 + 单字符插入扰动

用法:
    python main.py   # 解码器验证 + 2 组实战样例 + roundtrip/插字符敏感性 (纯 Python, 无网络)

原理 (qdjiangzhiyun.js 的 decode_content(), 2024-10 原项目抓取):
    章节页 HTML 内嵌 JS: var rid = parseInt("4522"); var rcontent = "...";
    正文 = 标准 Base64, 在 rid 下标处插入了 1 个垃圾字符 (抗正则直接提取)
    解码: rcontent 去掉 rid 位置的字符 -> base64 解码 -> UTF-8
    清洗: <br /> -> 换行 (原项目 pandas 阶段处理, 页面用 <br /> 表示段落)

样例来源: qdjiangzhiyun.js 内嵌 2 组完整章节 (rid=4522 激活 / rid=8384 注释),
          期望值 = 原版 JS 经 node 实跑输出交叉验证一致 (2026-08-20 复验).
"""

import base64
import hashlib
import json
import os
import random
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

DIR = os.path.dirname(os.path.abspath(__file__))


def load_samples() -> list:
    with open(os.path.join(DIR, "samples.json"), encoding="utf-8") as f:
        return json.load(f)


def decode_content(rid: int, rcontent: str) -> str:
    """对应 JS decode_content(rid, rcontent): 去 rid 处垃圾字符 -> 标准 base64 -> UTF-8"""
    cleaned = rcontent[:rid] + rcontent[rid + 1:]
    return base64.b64decode(cleaned).decode("utf-8")


def encode_content(plain: str) -> tuple:
    """加密方向 (逆过程): UTF-8 -> base64 -> 随机位置插入 1 个垃圾字符, 返回 (rid, rcontent)"""
    b64 = base64.b64encode(plain.encode("utf-8")).decode()
    rid = random.randrange(0, len(b64) + 1)
    junk = random.choice("qwertyuiopasdfghjklzxcvbnm")
    return rid, b64[:rid] + junk + b64[rid:]


def clean_br(text: str) -> str:
    """段落清洗: <br /> -> 换行 (页面内嵌 JS 输出的原始形态)"""
    return text.replace("<br />", "\n")


def main() -> None:
    passed, total = 0, 0

    def check(ok: bool, label: str, detail: str = "") -> None:
        nonlocal passed, total
        total += 1
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label} {detail}")

    samples = load_samples()

    # 1. 样例文件结构
    check(len(samples) == 2 and all(k in samples[0] for k in
          ("rid", "rcontent", "head", "tail", "sha256")),
          "samples.json structure", f"({len(samples)} samples)")
    check(samples[0]["rid"] == 4522 and samples[1]["rid"] == 8384,
          "sample rid values", "(4522 active / 8384 comment in source JS)")

    # 2. 实战样例解码: sha256 + 首尾片段三重断言
    for s in samples:
        plain = decode_content(s["rid"], s["rcontent"])
        h = hashlib.sha256(plain.encode("utf-8")).hexdigest()
        ok = (h == s["sha256"] and len(plain) == s["plain_len"]
              and plain.startswith(s["head"]) and plain.endswith(s["tail"]))
        check(ok, f"decode sample rid={s['rid']}",
              f"(plain {len(plain)} chars, sha256 {h[:12]}...)")

    # 3. 段落清洗: <br /> 全部转行, 无残留
    s0 = samples[0]
    plain = decode_content(s0["rid"], s0["rcontent"])
    cleaned = clean_br(plain)
    br_count = plain.count("<br />")
    check(cleaned.count("<br />") == 0 and cleaned.count("\n") == br_count,
          "clean_br transform",
          f"({br_count} <br /> -> {cleaned.count(chr(10))} newlines)")

    # 4. 插字符敏感度: 垃圾字符必须删除且位置必须正确
    #    a) 不删: 标准 base64 解码失败或错位
    try:
        wrong_plain = base64.b64decode(s0["rcontent"]).decode("utf-8")
        wrong_ok = wrong_plain != plain
    except Exception:
        wrong_ok = True
    check(wrong_ok, "junk char must be removed",
          "(raw b64decode fails or shifts)")

    #    b) 删错位置 (rid+1): 解码错位 -> 结果不同或 UTF-8 直接非法
    off = s0["rcontent"][:s0["rid"] + 1] + s0["rcontent"][s0["rid"] + 2:]
    try:
        wrong2 = base64.b64decode(off).decode("utf-8")
        wrong2_ok = wrong2 != plain
        detail = f"(delete at rid+1 gives: {wrong2[:20]!r}...)"
    except UnicodeDecodeError:
        wrong2_ok = True
        detail = "(delete at rid+1 -> not valid UTF-8)"
    check(wrong2_ok, "junk char position matters", detail)

    # 5. roundtrip: 加密方向 (b64 + 插字符) -> 解码还原原文
    rid, rcontent = encode_content(plain)
    check(decode_content(rid, rcontent) == plain,
          "roundtrip encode->decode", f"(rid={rid}, rcontent {len(rcontent)} chars)")

    # 6. 等价性证明: 真实样例的明文 re-encode 后去掉垃圾字符 == 原始 rcontent 去掉垃圾字符
    back = base64.b64encode(plain.encode("utf-8")).decode()
    check(back == s0["rcontent"][:s0["rid"]] + s0["rcontent"][s0["rid"] + 1:],
          "encode is exact inverse", "(b64encode(plain) == splice(rcontent))")

    print(f"\n{passed}/{total} passed")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
