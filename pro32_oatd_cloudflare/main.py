"""
pro32 oatd.org Cloudflare Turnstile 应对 — 状态机判别 + 挑战类型检测 + 拟人轨迹

收录 多探科技/pro4_oatd 的 Cloudflare Cookie 刷新方案中「可离线验证」的确定性
环节 (原版见同目录 cookie_flush_playwright_cdp.py, 生产使用中):

    1. Turnstile 状态机判别  — 原版 _ts_state() 的 Python 等价实现:
       none → loading → ready → verifying → solved 五态 + slow_down
       依据页面 title / 挑战 iframe / spinner 等 DOM 特征判定
    2. 挑战类型检测        — 原版 _detect_cloudflare():
       cType: 'non-interactive' | 'managed' | 'interactive' + embedded
    3. 拟人鼠标轨迹        — 原版 _human_mouse_move() 的三次贝塞尔轨迹生成:
       控制点随机偏移 + 中段微抖动 + 两端慢中间快 (参数化版, 便于确定性验证)

⚠️ 完整 Cookie 刷新链路 (启动真实 Chrome → 点击 Turnstile → 提取 cf_clearance)
   依赖真实浏览器与目标站点, 不在离线验证范围内; 方案细节见 ANALYSIS.md。

用法:
    python main.py            # 状态机/类型/轨迹三类样例, 输出即验证

样例说明: 状态机与类型样例为「合成 HTML 用例」 (按原版判定要素构造),
         轨迹样例为参数化确定性用例 — 非真实抓包, 用途是验证判定逻辑本身。
"""

import re

# ---------------------------------------------------------------- 核心复现 1: 状态机
def ts_state(html: str) -> str:
    """复现 cookie_flush_playwright_cdp.py 的 _ts_state() 判定逻辑。

    原版在浏览器 page.evaluate 中查询 DOM; 本实现以 HTML 字符串为输入,
    用正则提取 title 与 body 文本 (模拟 innerText), 判定顺序与原版一致:

      slow_down → ready/verifying (有挑战 iframe/widget) → verifying (spinner)
      → loading (challenge form + 标题特征) → none
    """
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    title = m.group(1) if m else ""
    body = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.S | re.I)
    body = re.sub(r"<[^>]+>", " ", body)

    if "Please slow down" in body or "Server Too Busy" in body:
        return "slow_down"

    has_ts_iframe = (
        'iframe' in html
        and 'src="https://challenges.cloudflare.com/cdn-cgi/challenge-platform' in html
    ) or ('src="https://challenges.cloudflare.com/cdn-cgi/challenge-platform' in html)
    has_widget = any(s in html for s in (
        'id="cf-turnstile"', 'id="cf_turnstile"', 'class="turnstile-wrapper"',
        'src="https://challenges.cloudflare.com/turnstile',
    ))
    has_challenge_form = any(s in html for s in (
        'id="challenge-form"', 'action="https://challenges.cloudflare.com"',
        'data-ray', 'class="main-content"',
    ))
    has_spinner = any(s in html for s in (
        'id="cf-challenge-running"', 'class="challenge-running"', 'class="lds-ring"',
        'class="spinning-wheel"', 'data-status="verifying"',
    ))
    has_title = any(s in title for s in ("Just a moment", "Cloudflare", "Attention Required"))
    is_verifying = "Verifying you are human" in body or "Verifying" in body or has_spinner

    if has_ts_iframe or has_widget:
        return "verifying" if is_verifying else "ready"
    if is_verifying:
        return "verifying"
    if has_challenge_form and has_title:
        return "loading"
    if has_title and not has_challenge_form:
        return "loading"
    return "none"


# ---------------------------------------------------------------- 核心复现 2: 挑战类型
def detect_cloudflare(html: str):
    """复现 _detect_cloudflare(): cType 三型 + embedded, 无则 None。"""
    for ctype in ("non-interactive", "managed", "interactive"):
        if "cType: '%s'" % ctype in html:
            return ctype
    if "challenges.cloudflare.com/turnstile/v" in html:
        return "embedded"
    return None


# ---------------------------------------------------------------- 核心复现 3: 拟人轨迹
def bezier_track(x0, y0, x1, y1, steps=20,
                 p=(0.3, 0.2, 0.0, 0.0, 0.7, 0.8, 0.0, 0.0),
                 jitter=0.0):
    """复现 _human_mouse_move() 的三次贝塞尔轨迹 (参数化确定性版)。

    p = (cp1_x比例, cp1_y比例, cp1_x抖动, cp1_y抖动, cp2_x比例, cp2_y比例,
         cp2_x抖动, cp2_y抖动); 原版比例/抖动取 uniform 随机, 此处参数化便于验证。
    返回 [(x, y), ...] 共 steps+1 点, 首尾精确为 (x0,y0)/(x1,y1)。
    """
    cp1_x = x0 + (x1 - x0) * p[0] + p[2]
    cp1_y = y0 + (y1 - y0) * p[1] + p[3]
    cp2_x = x0 + (x1 - x0) * p[4] + p[6]
    cp2_y = y0 + (y1 - y0) * p[5] + p[7]

    points = []
    for i in range(steps + 1):
        t = i / steps
        x = ((1 - t) ** 3 * x0 + 3 * (1 - t) ** 2 * t * cp1_x
             + 3 * (1 - t) * t ** 2 * cp2_x + t ** 3 * x1)
        y = ((1 - t) ** 3 * y0 + 3 * (1 - t) ** 2 * t * cp1_y
             + 3 * (1 - t) * t ** 2 * cp2_y + t ** 3 * y1)
        if 2 < i < steps - 2:          # 原版: 中段微抖动 (手抖模拟)
            x += jitter
            y += jitter
        points.append((x, y))
    return points


# ---------------------------------------------------------------- 样例验证
# (输入, 期望) — 三类确定性环节的合成用例
STATE_CASES = [
    # 挑战 iframe 已渲染且未在验证 → ready
    ('<title>Just a moment...</title><body>'
     '<iframe src="https://challenges.cloudflare.com/cdn-cgi/challenge-platform"></iframe></body>',
     "ready"),
    # 挑战 iframe + Verifying 文案 → verifying
    ('<title>Just a moment...</title><body>Verifying you are human'
     '<iframe src="https://challenges.cloudflare.com/cdn-cgi/challenge-platform"></iframe></body>',
     "verifying"),
    # 标题特征 + challenge-form 但 widget 未渲染 → loading
    ('<title>Just a moment...</title><body><div id="challenge-form"></div></body>',
     "loading"),
    # 限速文案 → slow_down (验证已过但被限速, 勿当失败)
    ('<title>Search</title><body>Server Too Busy - Please slow down</body>',
     "slow_down"),
    # 正常业务页 (无 CF 特征) → none
    ('<title>OATD Search</title><body><div id="facets">Search Limiters</div></body>',
     "none"),
]

TYPE_CASES = [
    ('<script>cType: \'non-interactive\'</script>', "non-interactive"),
    ('<script>cType: \'managed\'</script>', "managed"),
    ('<script>cType: \'interactive\'</script>', "interactive"),
    ('<iframe src="https://challenges.cloudflare.com/turnstile/v0/api.js"></iframe>',
     "embedded"),
    ('<html>正常页面</html>', None),
]

# 轨迹用例: (起点, 终点, 参数, 期望性质)
TRACK_CASES = [
    ((100, 100), (700, 300), dict(steps=20, p=(0.3, 0.2, 0.0, 0.0, 0.7, 0.8, 0.0, 0.0), jitter=0.0)),
    ((300, 500), (600, 200), dict(steps=30, p=(0.25, 0.15, 10.0, -5.0, 0.65, 0.85, -8.0, 4.0), jitter=1.0)),
    ((50, 50), (50, 50), dict(steps=10, p=(0.3, 0.2, 0.0, 0.0, 0.7, 0.8, 0.0, 0.0), jitter=0.0)),
]


def main() -> None:
    passed = total = 0

    print("== Turnstile 状态机判别 ==")
    for html, expected in STATE_CASES:
        total += 1
        got = ts_state(html)
        ok = got == expected
        passed += ok
        print("[%s] %-12s (期望 %s)" % ("PASS" if ok else "FAIL", got, expected))

    print("\n== 挑战类型检测 ==")
    for html, expected in TYPE_CASES:
        total += 1
        got = detect_cloudflare(html)
        ok = got == expected
        passed += ok
        print("[%s] %-16s (期望 %s)" % ("PASS" if ok else "FAIL", str(got), expected))

    print("\n== 拟人轨迹性质 ==")
    for (x0, y0), (x1, y1), kw in TRACK_CASES:
        total += 1
        pts = bezier_track(x0, y0, x1, y1, **kw)
        steps = kw["steps"]
        ok = (len(pts) == steps + 1
              and abs(pts[0][0] - x0) < 1e-9 and abs(pts[0][1] - y0) < 1e-9
              and abs(pts[-1][0] - x1) < 1e-9 and abs(pts[-1][1] - y1) < 1e-9
              and all(abs(pts[i][0] - pts[i - 1][0]) <= 200
                      and abs(pts[i][1] - pts[i - 1][1]) <= 200
                      for i in range(1, len(pts))))
        passed += ok
        print("[%s] 起点(%d,%d) -> 终点(%d,%d), %d 点, 抖动=%.1f"
              % ("PASS" if ok else "FAIL", x0, y0, x1, y1, len(pts), kw["jitter"]))

    print("\n%d/%d 通过" % (passed, total))
    if passed != total:
        raise SystemExit(1)


# ---------------------------------------------------------------- 可选: 真实 Cookie 刷新
# 完整链路 (不可离线): CookieFlush → 启动全新 Chrome(独立 user-data-dir + CDP)
#   → stealth.min.js 注入 → 状态机过 Turnstile → 拟人点击 → context.cookies()
#   → test_cookie requests 实测 → 返回 {cf_clearance: ...} 供主爬虫 requests 携带
# 详见同目录 cookie_flush_playwright_cdp.py (生产方案) 与 ANALYSIS.md (研究文档)。

if __name__ == "__main__":
    main()
