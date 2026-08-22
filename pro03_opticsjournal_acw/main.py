"""
中国光学期刊网 (opticsjournal.net) — 阿里云 WAF acw_sc__v2 cookie 生成

用法:
    python main.py            # 运行 2 组实战样例 + 1 组逆变换自洽验证

原理:
    首次请求返回 JS 挑战页 (error.js, OB 混淆 + 反调试), 内嵌 var arg1='...';
    挑战 JS 计算 arg2 = hexXor(unsbox(arg1), 固定key), 写 cookie acw_sc__v2 后
    reload 页面。算法完全静态:
        1. unsbox: 固定 40 位置换表重排 (结果第 j 位 = 源第 table[j]-1 位)
        2. hexXor: 每 2 个 hex 字符一组, 与固定 key "3000176000..." 异或
    无随机性, Python 直接掉包, 无需执行混淆 JS。

样例来源: 2025-07 抓包（get_arg2.js 注释 / error_decoded.js 挑战页）
"""

# 固定置换表 (unsbox), 1~40 的排列, 与 JS _0x4b082b 一致
UNSBOX_TABLE = [
    0xf, 0x23, 0x1d, 0x18, 0x21, 0x10, 0x1, 0x26, 0xa, 0x9,
    0x13, 0x1f, 0x28, 0x1b, 0x16, 0x17, 0x19, 0xd, 0x6, 0xb,
    0x27, 0x12, 0x14, 0x8, 0xe, 0x15, 0x20, 0x1a, 0x2, 0x1e,
    0x7, 0x4, 0x11, 0x5, 0x3, 0x1c, 0x22, 0x25, 0xc, 0x24,
]
HEX_XOR_KEY = "3000176000856006061501533003690027800375"  # 固定 key, 40 字符


def unsbox(s: str) -> str:
    """复现 JS String.prototype.unsbox(): 按置换表重排。

    对应 JS (get_arg2.js):
        out[j] = s[i] 其中 table[j] == i+1  =>  结果第 j 位 = 源第 table[j]-1 位
    """
    return "".join(s[v - 1] for v in UNSBOX_TABLE if v <= len(s))


def hex_xor(a: str, b: str) -> str:
    """复现 JS String.prototype.hexXor(): 每 2 个 hex 字符一组异或, 结果补零。

    对应 JS:
        parseInt(a.slice(i,i+2),16) ^ parseInt(b.slice(i,i+2),16) -> toString(16), 1 位补 0
    """
    out = []
    for i in range(0, min(len(a), len(b)), 2):
        out.append(f"{int(a[i:i+2], 16) ^ int(b[i:i+2], 16):02x}")
    return "".join(out)


def get_arg2(arg1: str) -> str:
    """完整算法: arg2 = hexXor(unsbox(arg1), key) -> acw_sc__v2 cookie 值"""
    return hex_xor(unsbox(arg1), HEX_XOR_KEY)


# (arg1, 期望 arg2) — 来自实战抓包, 期望值经原 JS 逻辑 (node) 交叉验证
SAMPLE_CASES = [
    ("A07B3202783CCB56A5C8E12165FA8D5ABC81F1CE",
     "6881a1c187408f146a36c4d18ea6640b84faccb4"),
    ("1BE274EA5756C559143C74D058B985C99B8B8961",
     "68808e7975b97b4b5a506599679bdce23069bb1e"),
]


def unsbox_inv(t: str) -> str:
    """unsbox 的逆变换: 源第 i 位 = 结果第 j 位, 其中 table[j] == i+1。
    用于自洽验证: unsbox_inv(hexXor(arg2, key)) == arg1
    """
    out = [""] * len(t)
    for i in range(len(t)):
        out[i] = t[UNSBOX_TABLE.index(i + 1)]
    return "".join(out)


def main() -> None:
    passed = 0
    for arg1, expected in SAMPLE_CASES:
        got = get_arg2(arg1)
        ok = got == expected
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] get_arg2({arg1[:8]}...)")
        if not ok:
            print(f"      expected: {expected}")
            print(f"      got     : {got}")

    # 集成验证: 逆变换往返 arg2 -> arg1 (XOR 对称 + 置换可逆)
    # 注意: unsbox 保留源字符串大小写(arg1 大写), hex_xor 输出小写, 比较时统一大小写
    for arg1, arg2 in SAMPLE_CASES:
        back = unsbox_inv(hex_xor(arg2, HEX_XOR_KEY))
        ok = back.upper() == arg1.upper()
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] roundtrip arg1={arg1[:8]}...")

    print(f"\n{passed}/{len(SAMPLE_CASES) * 2} passed")
    if passed != len(SAMPLE_CASES) * 2:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
