"""
基于 Scrapling _cloudflare_solver 逻辑的 Cloudflare Cookie 刷新器。

改进：
- stealth.min.js 反检测注入
- Turnstile widget DOM 生命周期驱动的状态机（不再依赖 URL 变化）
- 点击前确保 widget 已渲染；点击后监控 widget 消失来判断验证完成
"""

import os
import signal
import time
from pathlib import Path
from random import randint
from re import compile as re_compile
from urllib.parse import quote, unquote, urlparse, urlunparse

import requests
from patchright.sync_api import sync_playwright

from util.tool import build_url_with_params

__CF_PATTERN__ = re_compile(r"^https?://challenges\.cloudflare\.com/cdn-cgi/challenge-platform/.*")

_STEALTH_JS_PATH = Path(__file__).parent / "stealth.min.js"


class CookieFlush:
    """基于 patchright + stealth.min.js + Turnstile 状态机的 CF Cookie 刷新器。"""

    def __init__(self, port=9223, headless=True):
        self.port = port
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self._browser_started = False

    # ── 浏览器生命周期 ──────────────────────────────────────────

    def _start_browser(self):
        if self._browser_started:
            return

        self._kill_browser_process(self.port)

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--window-size=1920,1080",
            ],
        )
        self.context = self.browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
            )
        )

        if _STEALTH_JS_PATH.exists():
            self.context.add_init_script(path=str(_STEALTH_JS_PATH))
            print(f"已注入 stealth.min.js")
        else:
            print(f"Warning: stealth.min.js 未找到 ({_STEALTH_JS_PATH})")

        self.page = self.context.new_page()
        self._browser_started = True
        print("浏览器已启动")

    @staticmethod
    def _kill_browser_process(port):
        try:
            find_port_cmd = f"lsof -t -i:{port}"
            pids = os.popen(find_port_cmd).read().strip().split("\n")
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

    def _get_page_content(self, max_retries=20):
        for _ in range(max_retries):
            try:
                return self.page.content() or ""
            except Exception:
                self.page.wait_for_timeout(500)
        raise RuntimeError("获取页面内容失败")

    def _wait_for_networkidle(self, timeout=5000):
        try:
            self.page.wait_for_load_state("networkidle", timeout=timeout)
        except Exception:
            pass

    def _wait_for_page_stability(self, load_dom=True, network_idle=True):
        self.page.wait_for_load_state("load")
        if load_dom:
            self.page.wait_for_load_state("domcontentloaded")
        if network_idle:
            self._wait_for_networkidle()

    # ── CF 检测 ─────────────────────────────────────────────────

    @staticmethod
    def _detect_cloudflare(page_content):
        for ctype in ("non-interactive", "managed", "interactive"):
            if f"cType: '{ctype}'" in page_content:
                return ctype
        if 'challenges.cloudflare.com/turnstile/v' in page_content:
            return "embedded"
        return None

    # ── Turnstile 状态机 ────────────────────────────────────────

    def _ts_state(self):
        """查询 Turnstile widget 的 DOM 状态。

        返回的 status 枚举:
            "none"       — 页面中没有 CF 挑战，可能已通过或不需要验证
            "loading"    — 页面标题有 "Just a moment"，但 Turnstile widget 还没渲染（转圈中）
            "ready"      — Turnstile checkbox/iframe 已渲染，可以点击
            "verifying"  — 已点击，正在验证中（spinner 可见）
            "solved"     — Turnstile 已从 DOM 消失，非 CF 页面，验证通过
            "slow_down"  — 访问频率过高提示
        """
        try:
            status = self.page.evaluate("""() => {
                const body = document.body ? document.body.innerText || '' : '';
                const title = document.title || '';
                const html = document.documentElement.outerHTML || '';

                // 频率限制
                if (body.includes('Please slow down') || body.includes('Server Too Busy')) {
                    return 'slow_down';
                }

                // Turnstile iframe（CF 挑战平台的 iframe）
                const tsIframe = document.querySelector(
                    'iframe[src*="challenges.cloudflare.com/cdn-cgi/challenge-platform"]'
                );
                // Turnstile widget 容器
                const tsWidget = document.querySelector(
                    '#cf-turnstile, #cf_turnstile, .turnstile-wrapper, ' +
                    'iframe[src*="challenges.cloudflare.com/turnstile"]'
                );
                // Challenge 表单
                const challengeForm = document.querySelector(
                    '#challenge-form, form[action*="challenges.cloudflare.com"], ' +
                    '[data-ray], .main-content'
                );

                // 验证 spinner：CF 的 loading 指示器
                const spinner = document.querySelector(
                    '#cf-challenge-running, .challenge-running, ' +
                    '.lds-ring, .spinning-wheel, ' +
                    '[data-status="verifying"], [aria-label*="verifying"]'
                );

                const hasTitle = title.includes('Just a moment') ||
                                 title.includes('请稍候') ||
                                 title.includes('Cloudflare') ||
                                 title.includes('Attention Required');

                const isVerifying = body.includes('Verifying you are human') ||
                                    body.includes('Verifying') ||
                                    !!spinner;

                // 状态判断
                if (tsIframe || tsWidget) {
                    // Turnstile widget 已加载
                    if (isVerifying) return 'verifying';
                    return 'ready';
                }

                if (isVerifying) return 'verifying';
                if (challengeForm && hasTitle) return 'loading';
                if (hasTitle && !challengeForm) return 'loading';

                // 没有 CF 特征 = 不在挑战中
                return 'none';
            }""")
            return status
        except Exception:
            return "none"

    def _wait_for_ts_state(self, target_states, timeout_seconds=30):
        """等待 Turnstile 进入目标状态之一，返回当前状态和耗时。

        Args:
            target_states: str 或 list — 目标状态(们)
            timeout_seconds: 超时秒数

        Returns:
            (final_state, elapsed_seconds)
        """
        if isinstance(target_states, str):
            target_states = [target_states]
        target_set = set(target_states)

        start = time.time()
        for _ in range(timeout_seconds * 2):  # 每 500ms 查一次
            state = self._ts_state()
            elapsed = time.time() - start
            if state in target_set:
                print(f"  Turnstile 状态 → '{state}' (耗时 {elapsed:.1f}s)")
                return state, elapsed
            self.page.wait_for_timeout(500)
        state = self._ts_state()
        elapsed = time.time() - start
        print(f"  Turnstile 等待超时 ({timeout_seconds}s)，当前状态: '{state}'")
        return state, elapsed

    # ── Cloudflare 挑战解决 ─────────────────────────────────────

    def _solve_cloudflare(self):
        """解决 Cloudflare Turnstile 挑战 — 基于 Turnstile 状态机。

        状态机流程:
            loading → ready → (click) → verifying → solved
        """

        # ── Phase 1：等待 widget 渲染（loading → ready） ──
        state = self._ts_state()
        print(f"  当前 Turnstile 状态: '{state}'")

        if state == "none":
            print("  ✓ 无需处理 CF 挑战")
            return None

        if state == "slow_down":
            print("  访问频率过高，等待 5s...")
            self.page.wait_for_timeout(5000)
            return None

        if state in ("loading",):
            print("  等待 Turnstile widget 渲染...")
            state, _ = self._wait_for_ts_state(["ready", "verifying"], timeout_seconds=20)
        elif state == "solved":
            print("  ✓ CF 已通过")
            return None

        if state not in ("ready", "verifying"):
            print(f"  意外状态 '{state}'，尝试继续...")

        # ── Phase 2：检测挑战类型并定位点击目标 ──
        page_content = self._get_page_content()
        challenge_type = self._detect_cloudflare(page_content) or "unknown"
        print(f"  挑战类型: \"{challenge_type}\"")

        # non-interactive：纯等待
        if challenge_type == "non-interactive":
            state, _ = self._wait_for_ts_state(
                ["solved", "none"], timeout_seconds=90
            )
            if state in ("solved", "none"):
                print("  ✓ 非交互式挑战已通过")
                return None

        # ── Phase 3：定位并点击 Turnstile 验证框 ──
        click_x, click_y = self._locate_turnstile_checkbox(challenge_type)
        if click_x is None:
            print("  ✗ 无法定位 Turnstile checkbox，重试...")
            self.page.wait_for_timeout(2000)
            return self._solve_cloudflare()

        print(f"  点击 Turnstile @ ({click_x}, {click_y})")
        self.page.mouse.click(click_x, click_y, delay=randint(100, 200), button="left")

        # ── Phase 4：等待验证完成（verifying → solved） ──
        print("  等待 CF 验证完成...")
        state, elapsed = self._wait_for_ts_state(
            ["solved", "none", "slow_down"], timeout_seconds=120
        )

        if state in ("solved", "none", "slow_down"):
            print(f"  ✓ CF 验证通过 (耗时 {elapsed:.0f}s)")
            self._wait_for_page_stability(load_dom=True, network_idle=True)
            return None

        # 如果超时但还在 verifying，再多等一会
        if state == "verifying":
            print("  验证还在进行中，再等 30s...")
            state, _ = self._wait_for_ts_state(
                ["solved", "none"], timeout_seconds=30
            )
            if state in ("solved", "none"):
                print("  ✓ CF 验证通过（二次等待后）")
                self._wait_for_page_stability(load_dom=True, network_idle=True)
                return None

        # 最后一次检查
        state = self._ts_state()
        if state in ("solved", "none"):
            print("  ✓ CF 已通过（最终检查）")
            return None

        print(f"  状态 '{state}'，递归重试...")
        return self._solve_cloudflare()

    def _locate_turnstile_checkbox(self, challenge_type):
        """定位 Turnstile 验证框的可点击坐标。

        Returns:
            (x, y) 或 (None, None)
        """
        box_selector = "#cf_turnstile div, #cf-turnstile div, .turnstile>div>div"
        if challenge_type != "embedded":
            box_selector = ".main-content p+div>div>div"

        outer_box = {}
        iframe = self.page.frame(url=__CF_PATTERN__)
        if iframe is not None:
            self._wait_for_page_stability(load_dom=True, network_idle=False)
            # 等待 iframe 可见
            for _ in range(30):
                try:
                    if iframe.frame_element().is_visible():
                        break
                except Exception:
                    pass
                self.page.wait_for_timeout(500)
            try:
                outer_box = iframe.frame_element().bounding_box()
            except Exception:
                pass

        if not iframe or not outer_box:
            try:
                outer_box = self.page.locator(box_selector).last.bounding_box()
            except Exception:
                pass

        if not outer_box:
            return None, None

        x = outer_box["x"] + randint(26, 28)
        y = outer_box["y"] + randint(25, 27)
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

        # ── 导航 ──
        print(f"导航到: {full_url[:100]}...")
        self.page.goto(full_url)
        self._wait_for_page_stability()

        # ── 初始状态 ──
        state = self._ts_state()
        print(f"初始 Turnstile 状态: '{state}'")

        # ── 处理 CF ──
        if state == "slow_down":
            print("访问频率过高，等待后重试...")
            self.page.wait_for_timeout(5000)
            self.page.goto(full_url)
            self._wait_for_page_stability()

        if state != "none":
            print("检测到 Cloudflare，开始解决...")
            self._solve_cloudflare()

        # ── 确认页面就绪 ──
        self._wait_for_page_stability(load_dom=True, network_idle=True)

        final_state = self._ts_state()
        page_content = self._get_page_content()
        if self.page.locator("#facets").count() > 0:
            print("#facets 已加载，页面就绪")
        elif "Please slow down..." in page_content:
            print("频率限制提示，但 CF 已通过")

        print(f"最终状态: '{final_state}'")

        # ── 多次提取 cookie（不重新导航） ──
        for retry in range(5):
            extra_wait = wait_sec + retry * 3
            print(f"等待 {extra_wait}s 后提取 (第 {retry + 1}/5)...")
            self.page.wait_for_timeout(extra_wait * 1000)

            cookies_list = self.context.cookies()
            cookies_dict = {
                c.get("name"): c.get("value") for c in cookies_list if c.get("name")
            }
            cf_clearance = cookies_dict.get("cf_clearance", "")
            if cf_clearance:
                print(f"  cf_clearance: {cf_clearance[:60]}...")
            else:
                print("  Warning: 未获取到 cf_clearance")

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
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
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
