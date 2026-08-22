"""
加速乐 (jiasule) WAF 521 挑战 — __jsl_clearance_s cookie 生成

用法:
    python main.py            # 运行 3 组实战样例，输出 cookie 与 hash 校验结果

原理:
    挑战页 HTML 内嵌 go({...}) 数据，含 bts/chars/ct/ha 四个关键字段。
    cookie = bts[0] + chars 中两字符 + bts[1]，暴力双循环枚举（chars 约 22
    字符 -> 最多 484 次 hash），直到 hash(cookie) == ct。ha 指定标准 hash
    算法（md5/sha1/sha256/sha512），可用 Python hashlib 直接掉包，无需执行
    混淆 JS。

样例来源: 2026-05 抓包（锦天城律所 www.allbrightlaw.com / 中金公司 www.cicc.com）
"""

import hashlib

# ha 字段 -> hashlib 算法名
HASH_ALGOS = {
    "md5": "md5",
    "sha1": "sha1",
    "sha256": "sha256",
    "sha512": "sha512",
}


def solve_cookie(data: dict) -> str:
    """复现 JS 挑战页的 get_cookie(): 暴力查找 chars 中的两个字符。

    对应 JS (main_兼容不同hash.js):
        for idx_1 / idx_2 双重循环, cookie = bts[0]+chars[i]+chars[j]+bts[1]
        if hash(cookie) === ct: return cookie
    """
    bts_0, bts_1 = data["bts"]
    chars = data["chars"]
    target = data["ct"]
    algo = HASH_ALGOS[data["ha"]]
    hash_func = getattr(hashlib, algo)

    for c1 in chars:
        for c2 in chars:
            cookie = bts_0 + c1 + c2 + bts_1
            if hash_func(cookie.encode()).hexdigest() == target:
                return cookie
    return ""


# (输入数据, 期望 cookie 值) — 全部来自实战抓包
SAMPLE_CASES = [
    (
        {
            "bts": ["1778049662.41|0|jZmQ", "pjUP9gw%2FVC9du8Q0vSe84%3D"],
            "chars": "FUYEtXpkETqffVXxELhYQJ",
            "ct": "6fe117dad643fc6f52c3712a7d15b4c7a0683a6158824ae9577160290772d2ec",
            "ha": "sha256",
        },
        "1778049662.41|0|jZmQXYpjUP9gw%2FVC9du8Q0vSe84%3D",
    ),
    (
        {
            "bts": ["1778039625.531|0|FXI", "luHCgKB6%2F7eCFKtQF6A1kU%3D"],
            "chars": "LvJjCOuSmCFzwFwIQaHMzg",
            "ct": "7f4476ca0a22a5649cffb07b9843fba9da1a910c",
            "ha": "sha1",
        },
        "1778039625.531|0|FXImFluHCgKB6%2F7eCFKtQF6A1kU%3D",
    ),
    (
        {
            "bts": ["1778053277.075|0|bpB", "42TpNqT2sPYF1%2FC9rYiDsg%3D"],
            "chars": "FUeMem8OxgYX6qGHbVcnPk",
            "ct": "7a538a8788333b5055256d3cd98eb0dcf5164cc1b05a98b3879e42575b4f81fd",
            "ha": "sha256",
        },
        "1778053277.075|0|bpB8642TpNqT2sPYF1%2FC9rYiDsg%3D",
    ),
]


def main() -> None:
    passed = 0
    for data, expected in SAMPLE_CASES:
        got = solve_cookie(data)
        algo = data["ha"]
        # 双重校验: cookie 值一致 + hash 自洽
        h = getattr(hashlib, HASH_ALGOS[algo])
        ok = got == expected and h(got.encode()).hexdigest() == data["ct"]
        passed += ok
        ins = got[len(data["bts"][0]):len(data["bts"][0]) + 2]
        print(f"[{'PASS' if ok else 'FAIL'}] ha={algo} inserted_chars={ins!r}")
        if not ok:
            print(f"      expected: {expected}")
            print(f"      got     : {got}")
    print(f"\n{passed}/{len(SAMPLE_CASES)} passed")
    if passed != len(SAMPLE_CASES):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
