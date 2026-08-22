"""
百度指数 (index.baidu.com) — 指数数据解密: 单表替换密码

用法:
    python main.py   # 解密器验证 + 真实三元组 + roundtrip + 空值处理 (纯 Python, 无网络)

原理 (index.py decrypt(), 2022-12 原项目抓包):
    GET /api/SearchApi/index?area=&word=&startDate=&endDate=  -> data.uniqid
    GET /Interface/ptbk?uniqid={uniqid}                       -> data = ptbk (解密钥匙)
    index_data (密文) 经 ptbk 单表替换 -> "109,121,174,..." 逗号分隔数字串
    n = len(ptbk)//2; 前 n 字符 = 密文字母表, 后 n 字符 = 明文字母表
    decrypt = dict(zip(ptbk[:n], ptbk[n:])) 逐字符替换; 空段 (",,") = 无数据 -> 0

    反爬: Cipher-Text header (登录态 base64, 未逆向), cookie 过期时需手动提供;
          JS 原版 decrypt 见前端 decrypt.js (for 循环版, 与本实现等价).

样例来源: test.ipynb cell 10 (2022-12-15 抓包), 期望值 = notebook 当时输出;
          output.json (2022-12-08) 为另一请求的明文结果, 用作 roundtrip 明文源.
"""

import hashlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

# 真实抓包三元组 (2022-12-15 test.ipynb cell 10)
PTBK = "WMmOaR5u3xjqerN.9-%48617205+,3"
CIPHER = ("ujMruxuru3ar3Rr3jr3ar3jr5ur55r3jr3jr5ur55r3jr55r3Nr5ur5qr5ur3jrq3rq3r5qrq3r5ur3ar5ur3jr5ur5jrr5jrrq3rrq3r5urrrq3rrr55rq3rq3r5ur3jr3arr5qr5jr3arujqrq3r5urq3rq3rrq3rrq3r5jr5qr5jr5ur5jr5ur5jrrrr5jrrrq3rrr5ur5jr5urq3rq3rq3rrq3rq3rrrq3rq3rq3rq3rq3rrq3r5jrrq3rrq3rq3rr5jrq3rq3rrrrrrrrq3rq3r5urq3rrrrrq3r5jr55rq3rrq3rrrq3rrq3r5jrrrrq3rrrrrr5jrq3rq3rq3rrrrrrq3rq3rq3r5jrrr5jrq3rq3rq3rrq3rrq3rrrq3rq3rrrrq3rrrrrrrrrrrrq3rrrrq3rrq3rq3rq3rrrrrrrrrrrrrq3r5jrrrq3rq3rrq3rr5jrq3rrrq3rrrrrrrrrrrrrrrrrrq3rrrrrrrq3rq3rq3rrrrrq3rrrrrrrrrrrrrrq3rrq3rrrrrq3rq3rrrrrrrrq3rrq3r5jrrrq3r5jr5jrrrr3Nr3Nr55rq3rr55rrrrrrq3rM5r5jr5jrr3jr5ur55r5urr5ur5jr5urrq3r3arux5rr5ur5jr5qrRxr5urq3r5urrrq3r5ur55rq3rq3r5ur55rq3r5jrMxr3arq3r5jr5ur55rr5Mr5ur5ur5jrq3r55rRxruaaraa3raxqrxNMruqurMxr3MrRNr3Mr5Mr3arRxr3jr3j")
PLAIN = ("109,121,174,78,70,74,70,61,66,70,70,61,66,70,66,73,61,65,61,70,57,57,65,57,61,74,61,70,61,60,,60,,57,,57,61,,,57,,,66,57,57,61,70,74,,65,60,74,105,57,61,57,57,,57,,57,60,65,60,61,60,61,60,,,,60,,,57,,,61,60,61,57,57,57,,57,57,,,57,57,57,57,57,,57,60,,57,,57,57,,60,57,57,,,,,,,,57,57,61,57,,,,,57,60,66,57,,57,,,57,,57,60,,,,57,,,,,,60,57,57,57,,,,,,57,57,57,60,,,60,57,57,57,,57,,57,,,57,57,,,,57,,,,,,,,,,,,57,,,,57,,57,57,57,,,,,,,,,,,,,57,60,,,57,57,,57,,60,57,,,57,,,,,,,,,,,,,,,,,,57,,,,,,,57,57,57,,,,,57,,,,,,,,,,,,,,57,,57,,,,,57,57,,,,,,,,57,,57,60,,,57,60,60,,,,73,73,66,57,,66,,,,,,57,96,60,60,,70,61,66,61,,61,60,61,,57,74,126,,61,60,65,82,61,57,61,,,57,61,66,57,57,61,66,57,60,92,74,57,60,61,66,,69,61,61,60,57,66,82,144,447,425,239,151,92,79,83,79,69,74,82,70,70")

# output.json 明文序列 (2022-12-08, 环境污染 all, 30 天) — roundtrip 明文源
REAL_SERIES = [832, 848, 833, 733, 746, 913, 867, 839, 921, 942, 755, 864, 1030,
               981, 1001, 1062, 1077, 845, 899, 1102, 1075, 1071, 1068, 988,
               806, 843, 985, 1053, 952, 984]


def build_tables(ptbk: str) -> tuple:
    """单表替换: (加密表, 解密表); n = len//2, 前半=密文字母表, 后半=明文字母表"""
    n = len(ptbk) // 2
    dec = dict(zip(ptbk[:n], ptbk[n:]))
    enc = {v: k for k, v in dec.items()}
    return enc, dec


def decrypt(ptbk: str, index_data: str) -> str:
    """对应 index.py decrypt(): 逐字符替换 -> 逗号分隔数字串 (空段 = 无数据)"""
    n = len(ptbk) // 2
    a = dict(zip(ptbk[:n], ptbk[n:]))
    return "".join([a[s] for s in index_data])


def encrypt(ptbk: str, plain: str) -> str:
    """加密方向 (逆过程): 明文数字串 -> 密文字符串"""
    _, dec = build_tables(ptbk)
    enc = {v: k for k, v in dec.items()}
    return "".join([enc[s] for s in plain])


def type_change(values: list) -> list:
    """对应 index.py typeChange(): 空段转 0"""
    return [0 if v == "" else int(v) for v in values]


def main() -> None:
    passed, total = 0, 0

    def check(ok: bool, label: str, detail: str = "") -> None:
        nonlocal passed, total
        total += 1
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label} {detail}")

    # 1. ptbk 结构: 偶数长度 / 前半密文表 / 后半明文表, 映射无冲突
    n = len(PTBK) // 2
    check(len(PTBK) == 2 * n and len(set(PTBK[:n])) == n and len(set(PTBK[n:])) == n,
          "ptbk structure", f"(len {len(PTBK)}, n={n})")

    # 2. 真实三元组: 密文 -> 明文逐字符一致 (全量断言)
    got = decrypt(PTBK, CIPHER)
    ok = (got == PLAIN
          and hashlib.sha256(got.encode()).hexdigest()
          == "d52ab79141ec3878b4b42a6abe4d165895804e2c3b0ecbf89a3923ab923a949b")
    check(ok, "real capture triple decrypt",
          f"({len(got)} chars -> sha256 {hashlib.sha256(got.encode()).hexdigest()[:12]}...)")

    # 3. 数值解析 + 空值处理: 366 个时段, 空段 -> 0
    nums = type_change(got.split(","))
    nonempty = sum(1 for v in nums if v != 0)
    check(len(nums) == 366 and nonempty < 366 and sum(nums) == 13877,
          "value parse + empty handling",
          f"({len(nums)} slots, {nonempty} non-empty, sum {sum(nums)})")

    # 4. roundtrip: 真实 ptbk 上 3 组不同明文 (含 output.json 真实序列)
    plain_inputs = [
        ",".join(str(v) for v in REAL_SERIES),          # 真实数据 (2022-12-08)
        "832,848,833,0,,1062",                          # 含空段
        "57,60,61,65,66,70,73,74,78,82,92,96,105",     # 短序列
    ]
    for i, p in enumerate(plain_inputs):
        c = encrypt(PTBK, p)
        ok = decrypt(PTBK, c) == p and all(ch in PTBK[:n] for ch in c)
        check(ok, f"roundtrip #{i}",
              f"(plain {len(p)} chars -> cipher {len(c)} chars)")

    # 5. 加密表完备性: 明文表每个字符都可逆 (enc->dec 恒等)
    _, dec = build_tables(PTBK)
    enc = {v: k for k, v in dec.items()}
    check(all(dec[enc[v]] == v for v in PTBK[n:]),
          "substitution is bijective", f"({n} symbol pairs)")

    print(f"\n{passed}/{total} passed")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
