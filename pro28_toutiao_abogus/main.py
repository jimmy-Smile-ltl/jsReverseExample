"""
pro28 今日头条 a_bogus — 补环境离线签名引擎

通过 Node.js 补环境 (toutiao_env_full.js + dom_prototypes.js) 加载头条原版
SDK (bdms_browser.js + sdk-glue.js + runtime_bundler_52.js), 离线生成:

    a_bogus  — 168/172 位 base64url 动态签名 (补环境档 168 位, 浏览器档 172 位)
    msToken  — 120 位 base64url 设备令牌 (原版从 localStorage.xmst 读取)

签名含随机/时间因子, 每次运行结果不同 → 样例用「长度 + 字符集」约束验证,
不做固定值比对。本文件只做 Python 侧校验, 签名计算由 Node 完成:

用法:
    python main.py            # 3 组参数 → 调 node toutiao_sign.js → 校验输出

依赖:
    node (v16+, 实测 v24)     # 必须
    Python 仅标准库           # subprocess 调用

样例来源: 2026-04~06 toutiao.com /api/pc/list/feed 接口抓包参数
(原项目: spider research/其他/pro3 今日头条 JS逆向/extract/)
"""

import json
import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SIGN_JS = os.path.join(BASE_DIR, "toutiao_sign.js")

# 实测签名字符集: 标准 base64 (+/) 与 URL-safe (-_) 混合, 无 padding
BOGUS_CHARS = set(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=_-"
)


def get_signature(params_str: str) -> dict:
    """调用 Node 签名模块, 返回 {a_bogus, msToken}。

    对齐原项目 extract/try_toutiao.py 的调用方式:
    node toutiao_sign.js "<params>" → stdout 为一行 JSON
    """
    result = subprocess.run(
        ["node", SIGN_JS, params_str],
        capture_output=True, text=True, timeout=60, cwd=BASE_DIR,
    )
    if result.returncode != 0:
        raise RuntimeError("Node 签名失败: %s" % result.stderr[-400:])
    return json.loads(result.stdout.strip().splitlines()[-1])


# ---------------------------------------------------------------- 样例验证
# (参数串, 允许的 a_bogus 长度集合, 期望 msToken 长度) — 参数取自 2026-04~06 抓包
SAMPLE_CASES = [
    # try_toutiao.py 主流程参数 (pc_profile_recommend 频道)
    ("channel_id=0&max_behot_time=0&category=pc_profile_recommend&aid=24&app_name=toutiao_web",
     {164, 168, 172}, 120),
    # env_git.js 内置抓包参数 (pc_profile_channel 频道, 含 msToken 原文)
    ("offset=0&channel_id=94349549395&max_behot_time=0&category=pc_profile_channel&disable_raw_data=true&aid=24&app_name=toutiao_web",
     {164, 168, 172}, 120),
    # 带分页游标的抓包参数
    ("offset=0&channel_id=3189398996&max_behot_time=1725964720&aid=24&app_name=toutiao_web",
     {164, 168, 172}, 120),
]


def main() -> None:
    passed = 0
    for params, bogus_lens, ms_len in SAMPLE_CASES:
        try:
            sig = get_signature(params)
            a_bogus, ms_token = sig["a_bogus"], sig["msToken"]
            ok = (len(a_bogus) in bogus_lens
                  and len(ms_token) == ms_len
                  and all(c in BOGUS_CHARS for c in a_bogus + ms_token))
            passed += ok
            print("[%s] params=%s..." % ("PASS" if ok else "FAIL", params[:50]))
            print("      a_bogus(%d)=%s..." % (len(a_bogus), a_bogus[:36]))
            print("      msToken(%d)=%s..." % (len(ms_token), ms_token[:28]))
            if not ok:
                print("      expected: a_bogus len in %s, msToken len=%d, base64url charset"
                      % (bogus_lens, ms_len))
        except Exception as e:
            passed += 0
            print("[FAIL] params=%s... 异常: %s" % (params[:50], e))
    print("\n%d/%d 通过" % (passed, len(SAMPLE_CASES)))
    if passed != len(SAMPLE_CASES):
        raise SystemExit(1)


# ---------------------------------------------------------------- 可选: 真实请求验证
# 真实请求 (需网络 + curl_cffi 绕过 TLS 指纹, 不进入 main 流程):
#   GET https://www.toutiao.com/api/pc/list/feed?<params>&a_bogus=<签名>&msToken=<令牌>
# 抓包步骤: F12 → Network → 过滤 /api/pc/list/feed → 复制 URL 参数
# 原项目 rpc/test_direct.py 浏览器方案实测: Status 200, Article count 12

if __name__ == "__main__":
    main()
