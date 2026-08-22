"""
社会舆情网 (shyq.org.cn) — 云锁 YunSuo WAF security_session_verify 挑战

用法:
    python main.py            # 运行 3 组实战样例，验证 hex 编码 + 挑战参数生成

原理:
    首访返回 JS 挑战页 (404-1.html):
        1. srcurl cookie = stringToHex(window.location.href)   # URL 转 hex
        2. 跳转 /?security_verify_data=stringToHex(width+","+height)
    带参请求后返回 404-2.html: 删除 srcurl, 跳回原页, 服务端下发
    security_session_verify / security_session_mid_verify cookie。
    核心加密仅为字符级 hex 编码 (JS charCodeAt().toString(16) == Python hex(ord())[2:]),
    无 key 无混淆, 直接掉包。

样例来源: 2025-08 抓包（挑战页 404-1.html / 404-2.html 内嵌真实数据）
"""

import re


def string_to_hex(s: str) -> str:
    """复现 JS 挑战页的 stringToHex(): 每个字符的 charCode 转小写 hex 后拼接。

    对应 JS (404-1.html):
        for (var i = 0; i < str.length; i++)
            val += str.charCodeAt(i).toString(16);
    """
    return "".join(hex(ord(c))[2:] for c in s)


def build_challenge(url: str, width: int, height: int) -> dict:
    """生成挑战所需的全部参数（纯计算，无网络）。

    返回:
        srcurl:              hex(url), 写进 srcurl cookie
        security_verify_data: hex(f"{width},{height}"), 附加到 URL 参数
        next_url:             挑战请求的完整 URL
    """
    screen_data = f"{width},{height}"
    return {
        "srcurl": string_to_hex(url),
        "security_verify_data": string_to_hex(screen_data),
        "next_url": f"{url}?security_verify_data={string_to_hex(screen_data)}",
    }


# (输入, 期望输出) — 来自实战抓包
SAMPLE_CASES = [
    ("1440,810", "313434302c383130"),                            # 屏幕数据, 404-2.html 的请求 URL 注释
    ("http://shyq.org.cn/", "687474703a2f2f736879712e6f72672e636e2f"),  # srcurl 首页值
    ("http://shyq.org.cn/list-yuqingdongtai.html",
     "687474703a2f2f736879712e6f72672e636e2f6c6973742d797571696e67646f6e677461692e68746d6c"),  # srcurl 列表页值
]


def main() -> None:
    passed = 0
    for raw, expected in SAMPLE_CASES:
        got = string_to_hex(raw)
        ok = got == expected
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] string_to_hex({raw!r})")
        if not ok:
            print(f"      expected: {expected}")
            print(f"      got     : {got}")

    # 挑战参数集成验证: 随机屏幕尺寸 (实战随机 1400-1800 x 800-1200)
    ch = build_challenge("http://shyq.org.cn/", 1440, 810)
    ok2 = ch["srcurl"] == SAMPLE_CASES[1][1] and ch["security_verify_data"] == SAMPLE_CASES[0][1]
    passed += ok2
    print(f"[{'PASS' if ok2 else 'FAIL'}] build_challenge -> {ch['next_url']}")

    print(f"\n{passed}/{len(SAMPLE_CASES) + 1} passed")
    if passed != len(SAMPLE_CASES) + 1:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
