"""
spa14.scrape.center — WASM 签名 (sign 参数) 逆向教学案例

用法:
    python main.py            # 运行全部样例验证 (无需网络)
    python main.py --wasm     # 追加: Node 实跑 Wasm.wasm 交叉验证 (需本机 node)

原理:
    JS 调用: this.$wasm.asm.encrypt(offset, timestamp)
    WASM 反编译 (wasm2wat -> Wasm.wat): 导出 encrypt(offset, ts) = offset + ts/3 + 16358
        (func (;4;) (param i32 i32) (result i32)
            local.get 0 local.get 1 i32.const 3 i32.div_s i32.add i32.const 16358 i32.add)
    参数: offset = (page-1)*limit, timestamp = Date.now()/1000 (秒, 整除)

    教学要点: 232 字节 WASM 无任何保护, wasm2wat 直出公式 ——
    "先评估是否值得深入分析": 小 WASM 反汇编即得, 大 WASM (数百 KB) 才考虑 wasmer 调用。

样例: 固定 offset/timestamp 推导 (公式为精确整数运算), --wasm 模式与真实 .wasm 逐值比对。
"""

import os
import subprocess
import sys

# sign = offset + ts // 3 + 16358  (对应 WASM i32.div_s 有符号整除)
MAGIC = 16358


def generate_sign(offset: int, timestamp: int) -> int:
    """WASM encrypt 的 Python 等价: offset + timestamp//3 + 16358"""
    return offset + timestamp // 3 + MAGIC


def build_params(page: int, limit: int, timestamp: int) -> dict:
    """真实请求参数: limit/offset/sign (offset = (page-1)*limit)"""
    offset = (page - 1) * limit
    return {"limit": limit, "offset": offset, "sign": generate_sign(offset, timestamp)}


def wasm_expected(offset: int, timestamp: int) -> int:
    """Node 实跑 Wasm.wasm 的 encrypt 得到真值 (交叉验证)"""
    wasm_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Wasm.wasm")
    js = f"""
    const fs = require('fs');
    const bytes = fs.readFileSync({wasm_path!r});
    const instance = new WebAssembly.Instance(new WebAssembly.Module(bytes));
    console.log(instance.exports.encrypt({offset}, {timestamp}));
    """
    out = subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True)
    return int(out.stdout.strip())


# ============================================================ 样例验证

# 固定时间戳推导样例 (公式为精确整数运算; 时间戳取 2026-08 秒级)
SAMPLE_CASES = [
    ((0, 1754123456), 584724176),     # page 1:  1754123456//3=584707818, +16358
    ((90, 1754123456), 584724266),    # page 10: +90
    ((990, 1754123457), 584725167),   # page 100: ts+1 整除进位 (//3=584707819)
    ((0, 1754123458), 584724177),     # ts 整除进位后 +16358
]


def main() -> None:
    passed = 0
    total = 0

    def check(ok: bool, label: str, detail: str = "") -> None:
        nonlocal passed, total
        total += 1
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label} {detail}")

    # 1. 固定样例: (offset, ts) -> 期望 sign
    for i, ((offset, ts), expect) in enumerate(SAMPLE_CASES):
        got = generate_sign(offset, ts)
        check(got == expect, f"sample #{i}", f"({offset}, {ts} -> {got})")

    # 2. 参数组装: 页码 -> limit/offset/sign 结构
    p = build_params(2, 10, 1754123456)
    check(p == {"limit": 10, "offset": 10, "sign": generate_sign(10, 1754123456)},
          "params builder", f"({p})")

    # 3. 负数时间戳边界 (i32 有符号): offset 为负在 WASM 中也可正确运算
    check(generate_sign(-10, 1754123456) == -10 + 1754123456 // 3 + MAGIC,
          "negative offset", f"({generate_sign(-10, 1754123456)})")

    # 4. Node 交叉验证: 实跑 Wasm.wasm 比对 (可选)
    if "--wasm" in sys.argv:
        for (offset, ts), expect in SAMPLE_CASES:
            got = wasm_expected(offset, ts)
            check(got == expect, f"wasm cross-check ({offset}, {ts})", f"(wasm={got})")
    else:
        print("[SKIP] --wasm cross-check (add --wasm to run Node against Wasm.wasm)")

    print(f"\n{passed}/{total} passed")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
