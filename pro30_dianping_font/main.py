"""
pro30 大众点评字体反爬 — PUA 码点 → glyph → 真实字符 还原

大众点评早期 (2022) 的字体反爬: 页面文字用自定义 WOFF 字体渲染,
真实字符 (数字 + 600 常用汉字) 的字形被随机分配到 Unicode PUA 私有区码点
(U+E000~U+F8FF)。直接抓 HTML 拿到的是乱码, 必须:

    1. 从页面 CSS 提取当次字体 URL → 下载 .woff
    2. fontTools 解析 woff 的 cmap 表: 码点 → glyph 名 (如 unie8cd)
    3. 用离线映射表 (npy, 保存 glyph 名 → 真实字符) 反查 → 明文

本复现覆盖 2/3 两步 (离线可验证); 第 1 步依赖站点 (已失效)。
6 组字体 (address / address-num / hours / review-shopdesc-dishname /
reviewTag / shopNum-tagName) 均为 2022-03 抓包存档。

关键机制: 每个字段类型用独立字体文件, 同一字符在不同字体中映射到
不同码点 (如 '1' 在 address 中是 0xe8cd, 在 address-num 中是 0xf271),
且每次访问可能更换字体 —— 映射表必须按次抓取。

用法:
    python main.py            # 7 组样例 (码点序列 → 明文) 逐组对照

依赖 (2 个第三方):
    pip install numpy fonttools

样例来源: 2022-03 大众点评店铺页抓包 (原项目: 无限集数/电商社交/大众点评/)
"""

import os

import numpy as np  # pip install numpy
from fontTools.ttLib import TTFont  # pip install fonttools

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

_FONT_FILES = ["address", "address-num", "hours",
               "review-shopdesc-dishname", "reviewTag", "shopNum-tagName"]


# ---------------------------------------------------------------- 核心复现
def load_mapping(font_name: str) -> dict:
    """加载 glyph 名 → 真实字符 映射表 (原项目以 .npy pickle dict 存档)。"""
    return np.load(os.path.join(BASE_DIR, font_name + ".npy"),
                   allow_pickle=True).item()


def decode_codepoints(font_name: str, codepoints: list) -> str:
    """把页面密文码点序列还原为真实文字 (对齐原 notebook 的还原流程)。

    codepoint → cmap 查 glyph 名 → npy 映射查真实字符。
    码点不在 cmap 或 glyph 不在映射表中时保留 '?'。
    """
    font = TTFont(os.path.join(BASE_DIR, font_name + ".woff"))
    cmap = font.getBestCmap()
    mapping = load_mapping(font_name)
    out = []
    for cp in codepoints:
        glyph = cmap.get(cp)
        out.append(mapping.get(glyph, "?") if glyph else "?")
    return "".join(out)


# ---------------------------------------------------------------- 样例验证
# (字体名, 码点序列, 期望明文) — 7 组取自 2022-03 抓包字体存档
SAMPLE_CASES = [
    ("address", [0xe8cd, 0xe1b9, 0xf3db, 0xf601, 0xf08b, 0xe1aa, 0xf86c, 0xf63c, 0xece9, 0xe37f], "1234567890"),
    ("address-num", [0xf271, 0xf413, 0xefd0, 0xeb59, 0xf701], "12345"),
    ("hours", [0xf763, 0xf27b, 0xecd0, 0xf1a3, 0xea49], "12345"),
    ("review-shopdesc-dishname", [0xed08, 0xf525, 0xefaa, 0xf1ec, 0xf7b2], "12345"),
    ("reviewTag", [0xe6f9, 0xe355, 0xf4dd, 0xf5c7, 0xef74], "12345"),
    ("shopNum-tagName", [0xe397, 0xf79a, 0xf778, 0xf7f8, 0xf760], "12345"),
    ("address", [0xe49c, 0xeabc, 0xf76c, 0xe95d, 0xea3a], "店中美家馆"),

]


def main() -> None:
    passed = 0
    for font_name, cps, expected in SAMPLE_CASES:
        got = decode_codepoints(font_name, cps)
        ok = got == expected
        passed += ok
        print("[%s] %-28s %s" % ("PASS" if ok else "FAIL", font_name, got))
        print("      码点: %s" % " ".join("0x%04x" % c for c in cps))
        if not ok:
            print("      expected: %s" % expected)
    print("\n%d/%d 通过" % (passed, len(SAMPLE_CASES)))
    if passed != len(SAMPLE_CASES):
        raise SystemExit(1)


# ---------------------------------------------------------------- 可选: 真实请求验证
# 站点已失效 (2022 抓包, 后续改版), 不复现第 1 步字体 URL 提取。
# 原流程: 店铺页 HTML → CSS 里 @font-face src → 下载 woff → 本脚本还原。

if __name__ == "__main__":
    main()
