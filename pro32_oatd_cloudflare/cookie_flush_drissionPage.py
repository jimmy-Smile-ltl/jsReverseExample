"""
基于 DrissionPage + Turnstile 状态机的 Cloudflare Cookie 刷新器。

核心改进（相比 Playwright 版）：
- DrissionPage 浏览器指纹特征不同，可能更容易绕过 CF bot 检测
- 用 page.title / page.ele() 直接查 DOM 检测 CF（跨域 iframe 内 JS 不可见）
- Turnstile widget DOM 生命周期驱动的状态机
- 点击前确认 widget 已渲染；点击后监控 widget 消失判断验证完成
"""

import os
import signal
import time
from pathlib import Path
from random import randint
from urllib.parse import quote, unquote, urlparse, urlunparse

import requests
from DrissionPage import ChromiumPage, ChromiumOptions

from util.tool import build_url_with_params

_STEALTH_JS_PATH = Path(__file__).parent / "stealth.min.js"


class CookieFlush:
    """基于 DrissionPage + Turnstile 状态机的 CF Cookie 刷新器。"""

    def __init__(self, port=9223, headless=True):
        self.port = port
        self.headless = headless
        self.page = None
        self._stealth_js = None
        self._browser_started = False

    # ── 浏览器生命周期 ──────────────────────────────────────────

    def _start_browser(self):
        if self._browser_started:
            return

        self._kill_browser_process(self.port)

        options = ChromiumOptions()
        options.headless(self.headless)
        options.set_argument("--no-sandbox")
        options.set_argument("--disable-gpu")
        options.set_argument("--disable-dev-shm-usage")
        options.set_argument("--disable-blink-features=AutomationControlled")
        options.set_argument("--window-size=1920,1080")
        options.set_local_port(self.port)

        self.page = ChromiumPage(addr_or_opts=options)

        # 注入 stealth.min.js（通过 CDP，所有页面生效）
        if _STEALTH_JS_PATH.exists():
            self._stealth_js = _STEALTH_JS_PATH.read_text(encoding="utf-8")
            self.page.run_cdp(
                "Page.addScriptToEvaluateOnNewDocument",
                source=self._stealth_js,
            )
            print("已注入 stealth.min.js (CDP)")
        else:
            print(f"Warning: stealth.min.js 未找到 ({_STEALTH_JS_PATH})")

        self._browser_started = True
        print("浏览器已启动 (DrissionPage)")

    @staticmethod
    def _kill_browser_process(port):
        try:
            pids = os.popen(f"lsof -t -i:{port}").read().strip().split("\n")
            if pids and pids[0]:
                print(f"端口 {port} 被占用，清理进程: {pids}")
                for pid in pids:
                    try:
                        os.kill(int(pid), signal.SIGKILL)
                    except Exception:
                        pass
                time.sleep(1)
        except Exception:
            pass

    # ── 页面工具 ────────────────────────────────────────────────

    def _html(self):
        try:
            return self.page.html or ""
        except Exception:
            return ""

    def _title(self):
        """获取页面标题（DrissionPage 原生属性，不走 JS）。"""
        try:
            return self.page.title or ""
        except Exception:
            return ""

    def _body_text(self, max_len=300):
        try:
            return (self.page.run_js(
                "return (document.body && document.body.innerText || '').substring(0, arguments[0])",
                max_len,
            ) or "")
        except Exception:
            return ""

    # ── CF 检测（DrissionPage 原生 API，不依赖 JS 跨域） ────────

    def _find_cf_iframe(self, timeout=5):
        """用 DrissionPage 原生 ele() 查找 CF 挑战 iframe。

        ele() 操作的是浏览器 DOM，能找到跨域 iframe 元素本身。
        """
        cf_selectors = [
            "tag:iframe@src*=challenges.cloudflare.com",
            "tag:iframe@src*=/cdn-cgi/challenge-platform",
        ]
        for sel in cf_selectors:
            ele = self.page.ele(sel, timeout=timeout)
            if ele:
                return ele
        return None

    def _find_target_content(self, timeout=2):
        """查找目标页面内容（非 CF 页面）。"""
        indicators = ["#facets", "#results", "div.result", "p.matchesReport"]
        for sel in indicators:
            ele = self.page.ele(sel, timeout=timeout)
            if ele:
                return True
        return False

    def _detect_cf_from_html(self, html):
        """从 HTML 文本中检测 CF 挑战类型。"""
        for ctype in ("non-interactive", "managed", "interactive"):
            if f"cType: '{ctype}'" in html:
                return ctype
        if 'challenges.cloudflare.com/turnstile/v' in html:
            return "embedded"
        if any(kw in html for kw in ["Just a moment...", "请稍候…", "请稍候"]):
            return "challenge_detected"
        if "challenges.cloudflare.com" in html:
            return "challenge_detected"
        if "/cdn-cgi/" in html:
            return "challenge_detected"
        return None

    def _is_on_cf(self):
        """多维度检测是否在 CF 挑战页面。

        使用 DrissionPage 原生 API + HTML 双重检测，
        不依赖 page.run_js() 因为 CF 内容在跨域 iframe 内。
        """
        # 1. 页面标题
        title = self._title()
        cf_titles = [
            "Just a moment...",
            "请稍候",
            "Cloudflare",
            "Attention Required",
        ]
        if any(t in title for t in cf_titles):
            return True, f"title='{title[:50]}'"

        # 2. CF iframe 存在
        cf_iframe = self._find_cf_iframe(timeout=1)
        if cf_iframe:
            return True, "cf_iframe_present"

        # 3. HTML 文本检测
        html = self._html()
        html_lower = html.lower()
        if "challenges.cloudflare.com" in html_lower:
            return True, "html_has_cf_url"
        if "just a moment" in html_lower:
            return True, "html_has_just_a_moment"
        if "/cdn-cgi/" in html:
            return True, "html_has_cdn_cgi"

        return False, "none"

    # ── Turnstile 状态机 ────────────────────────────────────────

    def _ts_state(self):
        """查询 Turnstile widget 的 DOM 状态。

        由于 CF iframe 是跨域的，JS 无法读取其内部内容，
        这里主要通过主页面 DOM 中 iframe 的存亡 + body text 来判断。

        Returns: "none" | "loading" | "ready" | "verifying" | "solved" | "slow_down"
        """
        try:
            state = self.page.run_js("""
            (() => {
                const body = document.body ? (document.body.innerText || '') : '';
                const title = document.title || '';

                if (body.includes('Please slow down') || body.includes('Server Too Busy')) {
                    return 'slow_down';
                }

                // 检测 CF challenge iframe（存在于主 DOM 中，可跨域检测到元素本身）
                const cfIframes = document.querySelectorAll(
                    'iframe[src*="challenges.cloudflare.com"], ' +
                    'iframe[src*="/cdn-cgi/challenge-platform"]'
                );

                // 验证 spinner / 文字
                const hasVerifying = body.includes('Verifying you are human') ||
                                    body.includes('Verifying') ||
                                    !!document.querySelector(
                                        '[aria-label*="verifying"], #cf-challenge-running, ' +
                                        '.lds-ring, .spinning-wheel'
                                    );

                if (cfIframes.length > 0) {
                    if (hasVerifying) return 'verifying';
                    return 'ready';
                }

                // 没有 iframe，但有 CF 标题
                const cfTitle = title.includes('Just a moment') ||
                                title.includes('请稍候') ||
                                title.includes('Cloudflare');
                if (cfTitle) return 'loading';
                if (hasVerifying) return 'verifying';

                // 页面有 CF 容器但没 iframe = 可能在加载
                if (document.querySelector('#challenge-form, [data-ray], .main-content') && cfTitle) {
                    return 'loading';
                }

                return 'none';
            })()
            """)
            return state or "none"
        except Exception:
            return "none"

    def _wait_ts_state(self, target_states, timeout_seconds=30):
        """等待 Turnstile 进入目标状态之一。"""
        if isinstance(target_states, str):
            target_states = [target_states]
        target_set = set(target_states)

        start = time.time()
        for _ in range(timeout_seconds * 2):
            state = self._ts_state()
            elapsed = time.time() - start
            if state in target_set:
                print(f"  TS 状态 → '{state}' ({elapsed:.1f}s)")
                return state, elapsed
            time.sleep(0.5)
        state = self._ts_state()
        elapsed = time.time() - start
        print(f"  TS 等待超时 ({timeout_seconds}s)，当前: '{state}'")
        return state, elapsed

    # ── Cloudflare 挑战解决 ─────────────────────────────────────

    def _solve_cloudflare(self):
        """解决 Cloudflare Turnstile 挑战 — Turnstile 状态机驱动。

        loading → ready → (click) → verifying → solved
        """
        # ── 先检测挑战类型 ──
        html = self._html()
        challenge_type = self._detect_cf_from_html(html) or "unknown"
        print(f"  挑战类型: \"{challenge_type}\"")

        state = self._ts_state()
        print(f"  当前 TS 状态: '{state}'")

        if state == "slow_down":
            print("  访问频率过高，等待 10s...")
            time.sleep(10)
            return None

        # ── Phase 1: loading → ready（等待 widget 渲染） ──
        if state in ("loading", "none") and challenge_type != "unknown":
            print("  等待 Turnstile widget 渲染...")
            state, _ = self._wait_ts_state(["ready", "verifying"], timeout_seconds=30)

        if state in ("none", "solved"):
            # 再检查一下是否真的没问题
            cf_iframe = self._find_cf_iframe(timeout=2)
            if cf_iframe:
                print("  CF iframe 存在但 TS 状态为 none，强行按 ready 处理")
                state = "ready"
            else:
                print("  ✓ 无需处理 CF 挑战")
                return None

        if state not in ("ready", "verifying", "loading"):
            print(f"  状态 '{state}'，等待 widget 出现...")
            state, _ = self._wait_ts_state(["ready", "verifying"], timeout_seconds=10)

        # ── Phase 2: non-interactive → 等待 ──
        if challenge_type == "non-interactive":
            state, _ = self._wait_ts_state(["solved", "none"], timeout_seconds=90)
            if state in ("solved", "none"):
                print("  ✓ 非交互式挑战已通过")
                return None

        # ── Phase 3: 定位并点击 Turnstile checkbox ──
        click_x, click_y = self._locate_turnstile(challenge_type)
        if click_x is None:
            print("  ✗ 无法定位 Turnstile checkbox，2s 后重试...")
            time.sleep(2)
            return self._solve_cloudflare()

        print(f"  点击 Turnstile @ ({click_x}, {click_y})")
        # 模拟人类点击行为
        self.page.actions.move_to(click_x, click_y)
        time.sleep(randint(80, 180) / 1000)
        self.page.actions.click(click_x, click_y)
        time.sleep(randint(50, 150) / 1000)
        self.page.actions.click(click_x, click_y)

        # ── Phase 4: verifying → solved ──
        print("  等待 CF 验证完成...")
        state, elapsed = self._wait_ts_state(
            ["solved", "none", "slow_down"], timeout_seconds=120
        )

        if state in ("solved", "none", "slow_down"):
            print(f"  ✓ CF 验证通过 ({elapsed:.0f}s)")
            return None

        # 还在 verifying，再等一会
        if state in ("verifying", "loading"):
            print("  验证进行中，再等 30s...")
            state, _ = self._wait_ts_state(["solved", "none"], timeout_seconds=30)
            if state in ("solved", "none"):
                print("  ✓ CF 已通过（二次等待）")
                return None

        # 最终检查：cf iframe 还在吗
        cf_iframe = self._find_cf_iframe(timeout=2)
        if not cf_iframe:
            print("  ✓ CF iframe 已消失，验证通过")
            return None

        # 目标页面内容出现了吗
        if self._find_target_content(timeout=2):
            print("  ✓ 目标页面内容已出现")
            return None

        print(f"  状态 '{state}'，重试...")
        time.sleep(1)
        return self._solve_cloudflare()

    def _locate_turnstile(self, challenge_type):
        """定位 Turnstile 验证框的可点击坐标。"""
        outer_box = None

        # 方法 1：找 CF challenge iframe
        iframe_ele = self._find_cf_iframe(timeout=3)
        if iframe_ele:
            rect = iframe_ele.rect
            outer_box = {
                "x": rect.viewport_location[0],
                "y": rect.viewport_location[1],
                "width": rect.size[0],
                "height": rect.size[1],
            }
            print(f"  定位到 CF iframe @ ({outer_box['x']}, {outer_box['y']}) "
                  f"{outer_box['width']}x{outer_box['height']}")

        # 方法 2：CSS 选择器
        if not outer_box:
            selectors = [
                ".main-content p+div>div>div",
                "#cf_turnstile div",
                "#cf-turnstile div",
                ".turnstile>div>div",
                "iframe[src*='challenges.cloudflare.com/turnstile']",
            ]
            if challenge_type == "embedded":
                selectors = [
                    "#cf_turnstile div",
                    "#cf-turnstile div",
                    ".turnstile>div>div",
                ]
            for sel in selectors:
                ele = self.page.ele(sel, timeout=1)
                if ele and ele.rect.size[0] > 0:
                    rect = ele.rect
                    outer_box = {
                        "x": rect.viewport_location[0],
                        "y": rect.viewport_location[1],
                        "width": rect.size[0],
                        "height": rect.size[1],
                    }
                    print(f"  定位到 checkbox 容器 '{sel}' @ ({outer_box['x']}, {outer_box['y']})")
                    break

        if not outer_box or outer_box.get("width", 0) <= 0:
            return None, None

        # 在 iframe 中间偏上位置点击（Turnstile checkbox 通常在 iframe 的上半部）
        x = int(outer_box["x"] + outer_box["width"] * 0.5 + randint(-2, 2))
        y = int(outer_box["y"] + outer_box["height"] * 0.4 + randint(-2, 2))
        return x, y

    # ── 公开接口 ────────────────────────────────────────────────

    def flush(self, url, params={}, wait_sec=2, headless=True):
        """访问目标 URL，解决 CF 挑战，返回有效 cookies。"""
        self._start_browser()

        full_url = (
            "https://oatd.org/oatd/search?"
            "q=%2A%3A%2A%20AND%20pub_dt%3A%5B2022-01-01T00%3A00%3A00Z%20TO%202023-01-01T00%3A00%3A00Z%5D"
        )
        cookies_dict = {}

        # ── 导航并等待页面稳定 ──
        print(f"导航到: {full_url[:100]}...")
        self.page.get(full_url)
        self.page.wait.load_start()

        # 等待 CF 内容可能需要的加载时间
        print("等待页面稳定（5s）...")
        time.sleep(5)

        # ── 诊断日志：页面实际状态 ──
        title = self._title()
        current_url = self.page.url
        print(f"  URL: {current_url[:120]}")
        print(f"  Title: '{title[:80]}'")

        # 用 DrissionPage 原生 API 检测 CF
        is_cf, reason = self._is_on_cf()
        print(f"  CF 检测: {is_cf} ({reason})")

        cf_iframe = self._find_cf_iframe(timeout=2)
        cf_type = self._detect_cf_from_html(self._html())
        ts_state = self._ts_state()
        print(f"  CF iframe: {'找到' if cf_iframe else '未找到'}")
        print(f"  CF 类型 (HTML): {cf_type or '未检测到'}")
        print(f"  TS 状态 (JS): '{ts_state}'")

        # ── 处理 ──
        if "Please slow down" in self._body_text() or "Server Too Busy" in self._body_text():
            print("访问频率过高，等待后重试...")
            time.sleep(10)
            self.page.get(full_url)
            self.page.wait.load_start()
            time.sleep(3)

        if is_cf or cf_type or cf_iframe:
            print(f"检测到 Cloudflare ({cf_type or reason})，开始解决...")
            self._solve_cloudflare()
        else:
            print("未检测到 CF 挑战")

        # ── 确认页面就绪 ──
        self.page.wait.load_start()
        time.sleep(2)

        html = self._html()
        state = self._ts_state()
        print(f"最终 TS 状态: '{state}'")
        if "#facets" in html:
            print("#facets 已加载，页面就绪")

        # ── 提取 cookie ──
        for retry in range(5):
            extra_wait = wait_sec + retry * 3
            print(f"等待 {extra_wait}s 后提取 (第 {retry + 1}/5)...")
            time.sleep(extra_wait)

            cookies_list = self.page.cookies()
            cookies_dict = {
                c.get("name"): c.get("value") for c in cookies_list if c.get("name")
            }
            cf_clearance = cookies_dict.get("cf_clearance", "")
            if cf_clearance:
                print(f"  cf_clearance: {cf_clearance[:60]}...")
            else:
                print(f"  当前 cookies: {list(cookies_dict.keys())}")

            if self.test_cookie(cookies_dict, full_url):
                print("  Cookie 验证成功")
                break
            else:
                print(f"  Cookie 尚未生效，继续等待...")

        return cookies_dict

    def test_cookie(self, cookies_dict, full_url):
        start_time = time.time()
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en,en-CN;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "cache-control": "max-age=0",
            "priority": "u=0, i",
            "sec-ch-ua": "\"Google Chrome\";v=\"147\", \"Not.A/Brand\";v=\"8\", \"Chromium\";v=\"147\"",
            "sec-ch-ua-arch": "\"x86\"",
            "sec-ch-ua-bitness": "\"64\"",
            "sec-ch-ua-full-version": "\"147.0.7727.55\"",
            "sec-ch-ua-full-version-list": "\"Google Chrome\";v=\"147.0.7727.55\", \"Not.A/Brand\";v=\"8.0.0.0\", \"Chromium\";v=\"147.0.7727.55\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-model": "\"\"",
            "sec-ch-ua-platform": "\"Linux\"",
            "sec-ch-ua-platform-version": "\"\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
        }
        if not cookies_dict:
            return False

        for retry in range(3):
            try:
                response = requests.get(
                    full_url, headers=headers, cookies=cookies_dict, timeout=10
                )
                if response is not None and response.status_code == 200:
                    print(f"  Cookie 可用，retry={retry}，耗时 {time.time() - start_time:.2f}s")
                    return True
            except Exception as e:
                print(f"  Cookie 测试超时 retry={retry}: {e}")
                time.sleep(5)
        return False

    def close(self):
        print("关闭浏览器...")
        try:
            if self.page:
                self.page.quit()
            self._browser_started = False
        except Exception as e:
            print(f"关闭浏览器时出错: {e}")
        print("浏览器已关闭")


# ── 直接运行测试 ────────────────────────────────────────────────

if __name__ == "__main__":
    cookies_flusher = CookieFlush(headless=False, port=9223)
    flush_url = "https://oatd.org"
    cookies_dict = cookies_flusher.flush(flush_url)
    print("获取到的 cookies：", {k: v[:40] + "..." for k, v in cookies_dict.items()})

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en,en-CN;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "cache-control": "max-age=0",
        "priority": "u=0, i",
        "sec-ch-ua": "\"Google Chrome\";v=\"147\", \"Not.A/Brand\";v=\"8\", \"Chromium\";v=\"147\"",
        "sec-ch-ua-arch": "\"x86\"",
        "sec-ch-ua-bitness": "\"64\"",
        "sec-ch-ua-full-version": "\"147.0.7727.55\"",
        "sec-ch-ua-full-version-list": "\"Google Chrome\";v=\"147.0.7727.55\", \"Not.A/Brand\";v=\"8.0.0.0\", \"Chromium\";v=\"147.0.7727.55\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": "\"\"",
        "sec-ch-ua-platform": "\"Linux\"",
        "sec-ch-ua-platform-version": "\"\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
    }
    search_url = "https://oatd.org/oatd/search"
    params = {"q": "*:* AND pub_dt:[1800-01-01T00:00:00Z TO 1801-01-01T00:00:00Z]"}
    if cookies_dict:
        for retry in range(5):
            response = requests.get(
                search_url, headers=headers, cookies=cookies_dict, params=params, timeout=10
            )
            print(f"检索测试 retry={retry}，status={response.status_code}")
            time.sleep(retry)

    cookies_flusher.close()
