"""
[项目名] — [一句话：复现什么加密/签名逻辑]

用法:
    python main.py            # 运行内置样例，输出对比结果
    python main.py --node     # 可选：备份路线 / Node 对拍（按需实现）

规范要求:
    1. 单文件、标准库优先，第三方依赖不得超过 2 个（在 README 中列明）
    2. SAMPLE_CASES 至少 3 组；含随机/时间的签名须固定随机源与时间后逐字节比对
    3. 真实请求验证不写进 main 主流程（避免依赖网络导致不可复现）
"""

import hashlib  # 按需替换为实际算法所需的库
# import base64, json, time ...
# 第三方依赖（如有）放这里并注明用途:
# from Crypto.Cipher import AES  # pip install pycryptodome


# ---------------------------------------------------------------- 核心复现
# [在这里实现从 JS 还原出的算法。命名和注释对齐 JS 原函数名，方便对照]

def encrypt_params(raw: str) -> str:
    """复现 JS 中的加密函数（原名: xxx）。

    要点（记录 JS→Python 的差异）:
    - JS 的 charCodeAt 对应 Python 的 ord()
    - 32 位整数溢出需手动 & 0xFFFFFFFF
    """
    # 还原逻辑...
    return hashlib.md5(raw.encode("utf-8")).hexdigest()  # 仅示例


# ---------------------------------------------------------------- 样例验证
# (输入, 期望输出) — 取自实战抓包，期望输出为当时 JS 的真实结果；
# 若算法含随机/时间，改用固定随机序列 + 固定时间生成的确定性向量
SAMPLE_CASES = [
    ("example_input_1", "expected_output_1"),
    ("example_input_2", "expected_output_2"),
    ("example_input_3", "expected_output_3"),
]


def main() -> None:
    passed = 0
    for raw, expected in SAMPLE_CASES:
        got = encrypt_params(raw)
        ok = got == expected
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] input={raw!r}")
        if not ok:
            print(f"      expected: {expected}")
            print(f"      got     : {got}")
    print(f"\n{passed}/{len(SAMPLE_CASES)} 通过")
    if passed != len(SAMPLE_CASES):
        raise SystemExit(1)


# ---------------------------------------------------------------- 可选: 真实请求验证
# 不进入 main 流程，手动调用。写清抓包步骤，便于接口变更时更新样例。
#
# def verify_live() -> None:
#     """抓包步骤: 打开 F12 → Network → 过滤 XHR → 复制 params 值"""
#     ...


# ---------------------------------------------------------------- 可选: 备份路线
# 原 SDK / 补环境 / Node 对拍放 reference/，用 --node 开关隔离；
# 未随仓库分发的第三方依赖在 README 注明获取方式与权利方。
#
# def node_signature(raw: str) -> str:
#     import subprocess
#     out = subprocess.run(["node", "reference/sign.js", raw], capture_output=True, text=True, check=True)
#     return out.stdout.strip()


if __name__ == "__main__":
    main()
