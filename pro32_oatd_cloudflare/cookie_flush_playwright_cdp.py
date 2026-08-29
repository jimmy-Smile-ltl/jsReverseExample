"""
基于 Playwright CDP 连接本地真实 Chrome 的 Cloudflare Cookie 刷新器。

与 cookie_flush_playwright.py 的核心区别：
- 每次启动全新的 Chrome 进程（独立 user-data-dir），不复用已有浏览器
- 真实 Chrome 浏览器没有自动化标记，指纹更自然，更容易绕过 CF bot 检测
- stealth.min.js 通过 CDP Page.addScriptToEvaluateOnNewDocument 注入
"""

import math
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from random import randint, uniform
from re import compile as re_compile

import requests
from playwright.sync_api import sync_playwright

__CF_PATTERN__ = re_compile(r"^https?://challenges\.cloudflare\.com/cdn-cgi/challenge-platform/.*")

_STEALTH_JS_PATH = Path(__file__).parent / "stealth.min.js"

_CHROME_PATHS = [
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "/opt/google/chrome/chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]


def _find_chrome():
    for p in _CHROME_PATHS:
        try:
            subprocess.run(["which", p], capture_output=True, check=True)
            return p
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    return None


class CookieFlush:
    """每次实例化启动全新 Chrome 进程的 CF Cookie 刷新器。"""

    def __init__(self, headless=True, port=None):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self._browser_started = False
        self._chrome_process = None
        self._user_data_dir = None
        self._cdp_port = port
        self._mouse_x = randint(300, 600)
        self._mouse_y = randint(200, 500)
        self._start_browser()

    # ── 浏览器生命周期 ──────────────────────────────────────────

    def _pick_free_port(self):
        """选一个空闲端口用于 CDP 调试。"""
        import socket
        # 用户指定了 就使用用户的
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", self._cdp_port))
                return self._cdp_port
        except OSError:
            pass
        # 报错 或者 没有指定 自己去找一个空闲的
        for port in range(9700, 9800):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("127.0.0.1", port))
                    return port
            except OSError:
                continue
        raise RuntimeError("无法找到空闲端口 (9700-9799)")

    def _start_chrome(self):
        """启动全新 Chrome 进程（独立 user-data-dir + 空闲端口）。

        不复用任何已有 Chrome 实例，每次都是独立窗口。
        """
        self._user_data_dir = tempfile.mkdtemp(prefix="chrome_cdp_")

        chrome_bin = _find_chrome()
        if not chrome_bin:
            raise RuntimeError(
                "未找到 Chrome/Chromium，请安装 google-chrome 或 chromium-browser"
            )

        self._cdp_port = self._pick_free_port()

        args = [
            chrome_bin,
            f"--remote-debugging-port={self._cdp_port}",
            f"--user-data-dir={self._user_data_dir}",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
            "--window-size=1920,1080",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            "--disable-sync",
            "--disable-translate",
            "--disable-background-networking",
            "--disable-features=TranslateUI,BlinkRuntimeCallStats,InterestFeedContentSuggestions",
            "--metrics-recording-only",
            "--mute-audio",
            "--safebrowsing-disable-auto-update",
            "--hide-scrollbars",
            "--ignore-certificate-errors",
            "--ignore-ssl-errors",
            "--new-window",
            "about:blank",
        ]

        if self.headless:
            args.insert(1, "--headless=new")

        print(f"启动全新 Chrome (port={self._cdp_port}, user_data_dir={self._user_data_dir})")
        self._chrome_process = subprocess.Popen(
            args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        print(f"Chrome PID={self._chrome_process.pid}")

        # 等待 CDP 就绪
        for _ in range(20):
            time.sleep(0.5)
            if self._check_cdp_port_alive():
                print("Chrome CDP 就绪")
                return
        raise RuntimeError(f"Chrome 启动了但 CDP 端口 {self._cdp_port} 无响应")

    def _check_cdp_port_alive(self):
        try:
            import json
            import urllib.request
            resp = urllib.request.urlopen(
                f"http://127.0.0.1:{self._cdp_port}/json/version", timeout=2
            )
            data = json.loads(resp.read().decode())
            if "Browser" in data:
                print(f"  检测到浏览器: {data.get('Browser', 'unknown')}")
                return True
        except Exception:
            pass
        return False

    def _start_browser(self):
        if self._browser_started:
            return

        self._start_chrome()

        cdp_url = f"http://127.0.0.1:{self._cdp_port}"
        self.playwright = sync_playwright().start()

        print(f"通过 CDP 连接到 Chrome ({cdp_url})...")
        self.browser = self.playwright.chromium.connect_over_cdp(cdp_url)

        # 创建新的隐身 context + 页面（不复用已有 target）
        self.context = self.browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
            )
        )
        self.page = self.context.new_page()
        print("创建独立 BrowserContext + 新页面")

        # 注入 stealth.min.js
        if _STEALTH_JS_PATH.exists():
            stealth_js = _STEALTH_JS_PATH.read_text(encoding="utf-8")
            try:
                cdp_session = self.context.new_cdp_session(self.page)
                cdp_session.send("Page.addScriptToEvaluateOnNewDocument", {"source": stealth_js})
                print("已注入 stealth.min.js (CDP)")
            except Exception as e:
                print(f"Warning: stealth.min.js CDP 注入失败: {e}")
        else:
            print(f"Warning: stealth.min.js 未找到 ({_STEALTH_JS_PATH})")

        self._browser_started = True
        print("浏览器已就绪 (独立 Chrome + CDP)")

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
            "loading"    — 页面标题有 "Just a moment"，但 Turnstile widget 还没渲染
            "ready"      — Turnstile checkbox/iframe 已渲染，可以点击
            "verifying"  — 已点击，正在验证中（spinner 可见）
            "solved"     — Turnstile 已从 DOM 消失，验证通过
            "slow_down"  — 访问频率过高提示
        """
        try:
            status = self.page.evaluate("""() => {
                const body = document.body ? document.body.innerText || '' : '';
                const title = document.title || '';

                if (body.includes('Please slow down') || body.includes('Server Too Busy')) {
                    return 'slow_down';
                }

                const tsIframe = document.querySelector(
                    'iframe[src*="challenges.cloudflare.com/cdn-cgi/challenge-platform"]'
                );
                const tsWidget = document.querySelector(
                    '#cf-turnstile, #cf_turnstile, .turnstile-wrapper, ' +
                    'iframe[src*="challenges.cloudflare.com/turnstile"]'
                );
                const challengeForm = document.querySelector(
                    '#challenge-form, form[action*="challenges.cloudflare.com"], ' +
                    '[data-ray], .main-content'
                );
                const spinner = document.querySelector(
                    '#cf-challenge-running, .challenge-running, ' +
                    '.lds-ring, .spinning-wheel, ' +
                    '[data-status="verifying"], [aria-label*="verifying"]'
                );

                const hasTitle = title.includes('Just a moment') ||
                                 title.includes('Cloudflare') ||
                                 title.includes('Attention Required');

                const isVerifying = body.includes('Verifying you are human') ||
                                    body.includes('Verifying') ||
                                    !!spinner;

                if (tsIframe || tsWidget) {
                    if (isVerifying) return 'verifying';
                    return 'ready';
                }

                if (isVerifying) return 'verifying';
                if (challengeForm && hasTitle) return 'loading';
                if (hasTitle && !challengeForm) return 'loading';

                return 'none';
            }""")
            return status
        except Exception:
            return "none"

    def _wait_for_ts_state(self, target_states, timeout_seconds=30):
        """等待 Turnstile 进入目标状态之一，返回当前状态和耗时。"""
        if isinstance(target_states, str):
            target_states = [target_states]
        target_set = set(target_states)

        start = time.time()
        for _ in range(timeout_seconds * 2):
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

    def _human_mouse_move(self, target_x, target_y, steps=None):
        """模拟人类鼠标移动轨迹（贝塞尔曲线 + 微抖动）。"""
        if steps is None:
            dist = math.hypot(target_x - self._mouse_x, target_y - self._mouse_y)
            steps = max(15, int(dist / 8))

        # 生成贝塞尔曲线控制点
        cp1_x = self._mouse_x + (target_x - self._mouse_x) * uniform(0.2, 0.4) + uniform(-80, 80)
        cp1_y = self._mouse_y + (target_y - self._mouse_y) * uniform(0.1, 0.3) + uniform(-60, 60)
        cp2_x = self._mouse_x + (target_x - self._mouse_x) * uniform(0.6, 0.8) + uniform(-40, 40)
        cp2_y = self._mouse_y + (target_y - self._mouse_y) * uniform(0.7, 0.9) + uniform(-30, 30)

        points = []
        for i in range(steps + 1):
            t = i / steps
            # 三次贝塞尔曲线
            x = ((1 - t) ** 3 * self._mouse_x
                 + 3 * (1 - t) ** 2 * t * cp1_x
                 + 3 * (1 - t) * t ** 2 * cp2_x
                 + t ** 3 * target_x)
            y = ((1 - t) ** 3 * self._mouse_y
                 + 3 * (1 - t) ** 2 * t * cp1_y
                 + 3 * (1 - t) * t ** 2 * cp2_y
                 + t ** 3 * target_y)
            # 微抖动（模拟手抖）
            if i > 2 and i < steps - 2:
                x += uniform(-1.5, 1.5)
                y += uniform(-1.5, 1.5)
            points.append((x, y))

        # 执行移动（非匀速，开始慢中间快结束慢）
        for i, (px, py) in enumerate(points):
            # 速度曲线：两端慢中间快
            progress = i / max(1, len(points) - 1)
            delay = 0.003 + 0.012 * (1 - abs(2 * progress - 1))
            self.page.mouse.move(px, py)
            time.sleep(delay)

        self._mouse_x, self._mouse_y = target_x, target_y

    def _human_click(self, target_x, target_y):
        """模拟人类点击：先移动到目标附近 → 移动到目标 → 点击。"""
        # 先移动到目标附近（不精确）
        near_x = target_x + uniform(-5, 5)
        near_y = target_y + uniform(-5, 5)
        self._human_mouse_move(near_x, near_y)

        # 短暂停顿（人类会确认位置）
        time.sleep(uniform(0.08, 0.2))

        # 精确移动到目标
        self._human_mouse_move(target_x, target_y, steps=randint(3, 6))

        # 点击前微小停顿
        time.sleep(uniform(0.05, 0.15))

        # 按下 → 停顿 → 释放（模拟真实点击）
        self.page.mouse.down(button="left")
        time.sleep(uniform(0.04, 0.1))
        self.page.mouse.up(button="left")

    def _solve_cloudflare(self):
        """解决 Cloudflare Turnstile 挑战 — 基于 Turnstile 状态机。

        loading → ready → (click) → verifying → solved
        """
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

        page_content = self._get_page_content()
        challenge_type = self._detect_cloudflare(page_content) or "unknown"
        print(f"  挑战类型: \"{challenge_type}\"")

        if challenge_type == "non-interactive":
            state, _ = self._wait_for_ts_state(["solved", "none"], timeout_seconds=90)
            if state in ("solved", "none"):
                print("  ✓ 非交互式挑战已通过")
                return None

        click_x, click_y = self._locate_turnstile_checkbox(challenge_type)
        if click_x is None:
            print("  ✗ 无法定位 Turnstile checkbox，重试...")
            self.page.wait_for_timeout(2000)
            return self._solve_cloudflare()

        print(f"  点击 Turnstile @ ({click_x}, {click_y})")
        self._human_click(click_x, click_y)

        print("  等待 CF 验证完成...")
        state, elapsed = self._wait_for_ts_state(
            ["solved", "none", "slow_down"], timeout_seconds=120
        )

        if state in ("solved", "none", "slow_down"):
            print(f"  ✓ CF 验证通过 (耗时 {elapsed:.0f}s)")
            self._wait_for_page_stability(load_dom=True, network_idle=True)
            return None

        if state == "verifying":
            print("  验证还在进行中，再等 30s...")
            state, _ = self._wait_for_ts_state(["solved", "none"], timeout_seconds=30)
            if state in ("solved", "none"):
                print("  ✓ CF 验证通过（二次等待后）")
                self._wait_for_page_stability(load_dom=True, network_idle=True)
                return None

        state = self._ts_state()
        if state in ("solved", "none"):
            print("  ✓ CF 已通过（最终检查）")
            return None

        print(f"  状态 '{state}'，递归重试...")
        return self._solve_cloudflare()

    def _locate_turnstile_checkbox(self, challenge_type):
        """定位 Turnstile 验证框的可点击坐标。"""
        box_selector = "#cf_turnstile div, #cf-turnstile div, .turnstile>div>div"
        if challenge_type != "embedded":
            box_selector = ".main-content p+div>div>div"

        outer_box = {}
        iframe = self.page.frame(url=__CF_PATTERN__)
        if iframe is not None:
            self._wait_for_page_stability(load_dom=True, network_idle=False)
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
        full_url = (
            "https://oatd.org/oatd/search?"
            "q=%2A%3A%2A%20AND%20pub_dt%3A%5B2022-01-01T00%3A00%3A00Z%20TO%202023-01-01T00%3A00%3A00Z%5D"
        )
        cookies_dict = {}

        print(f"导航到: {full_url[:100]}...")
        self.page.goto(full_url)
        self._wait_for_page_stability()

        state = self._ts_state()
        print(f"初始 Turnstile 状态: '{state}'")

        if state == "slow_down":
            print("访问频率过高，等待后重试...")
            self.page.wait_for_timeout(5000)
            self.page.goto(full_url)
            self._wait_for_page_stability()

        if state != "none":
            print("检测到 Cloudflare，开始解决...")
            self._solve_cloudflare()

        self._wait_for_page_stability(load_dom=True, network_idle=True)

        final_state = self._ts_state()
        page_content = self._get_page_content()
        if self.page.locator("#facets").count() > 0:
            print("#facets 已加载，页面就绪")
        elif "Please slow down..." in page_content:
            print("频率限制提示，但 CF 已通过")
        elif self.page.locator("#ticker").count() > 0:
            print("#ticker 已加载，页面就绪")
        print(f"最终状态: '{final_state}'")

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
        print("关闭连接...")
        try:
            if self.page:
                self.page.close()
        except Exception:
            pass
        try:
            if self.context:
                self.context.close()
        except Exception:
            pass
        try:
            if self.browser:
                self.browser.close()
        except Exception:
            pass
        try:
            if self.playwright:
                self.playwright.stop()
        except Exception:
            pass
        self._browser_started = False

        # 关闭 Chrome 进程
        if self._chrome_process:
            try:
                self._chrome_process.terminate()
                self._chrome_process.wait(timeout=5)
                print("Chrome 进程已关闭")
            except Exception:
                try:
                    self._chrome_process.kill()
                except Exception:
                    pass

        # 清理临时 user-data-dir
        if self._user_data_dir and os.path.isdir(self._user_data_dir):
            try:
                shutil.rmtree(self._user_data_dir, ignore_errors=True)
                print(f"已清理临时目录: {self._user_data_dir}")
            except Exception:
                pass

        print("已关闭")


# ── 直接运行测试 ────────────────────────────────────────────────

if __name__ == "__main__":
    cookies_flusher = CookieFlush(headless=False)
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
