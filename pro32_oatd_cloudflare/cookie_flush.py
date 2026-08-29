from urllib.parse import quote, unquote, urlparse, urlunparse
from util.tool import build_url_with_params
import requests
import os
import signal
import time
from DrissionPage import ChromiumPage, ChromiumOptions
import pyautogui
# 部分ip 会非常卡吨 不知道为什么 加载很久 需要
class CookieFlush:
    """Ovid PDF 获取器，复用浏览器实例"""

    def __init__(self,port = 9223,headless= True):
        """初始化时启动浏览器"""
        print("正在配置浏览器参数...")
        # self.kill_browser_process(port)
        options = ChromiumOptions()
        #
        # # 1. 启用无头模式（Linux 服务器环境必须）
        options.headless(headless)

        # 2. 基础稳定性参数
        options.set_argument('--no-sandbox')  # 绕过操作系统安全沙箱（Linux 必备）
        options.set_argument('--disable-gpu')  # 禁用 GPU 加速（无头模式推荐）
        options.set_argument('--disable-dev-shm-usage')  # 解决 Linux 内存共享不足导致的崩溃
        options.set_argument('--window-size=1920,1080')  # 显式设置窗口大小，防止布局错乱
        options.set_local_port(port)
        # options.set_argument(
        #     '--header=Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8')
        # options.set_user_agent(
        #     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
        # # 3. 伪装参数
        options.set_argument('--disable-blink-features=AutomationControlled')
        # options.set_local_port(9222)
        self.page = ChromiumPage(addr_or_opts=options)



    def kill_browser_process(self,port):
        """
        根据端口号关闭残留的浏览器进程
        """
        try:
            # 使用 lsof 查找占用指定端口的 PID
            # -t 选项只返回 PID
            find_port_cmd = f"lsof -t -i:{port}"
            pids = os.popen(find_port_cmd).read().strip().split('\n')

            if pids and pids[0]:
                print(f"检测到端口 {port} 被占用，准备清理进程: {pids}")
                for pid in pids:
                    try:
                        os.kill(int(pid), signal.SIGKILL)
                        print(f"已杀死进程 PID: {pid}")
                    except Exception as e:
                        print(f"杀进程 {pid} 失败: {e}")
                time.sleep(1)  # 等待系统释放资源
            else:
                print(f"端口 {port} 是干净的，无需清理。")
        except Exception as e:
            print(f"清理端口时出错: {e}")
    def safe_encode_url(self,url):
        """
        对URL进行安全规范化编码：
        1. 先尝试解码（防止传入已编码内容导致二次编码）
        2. 重新按照标准RFC 3986进行编码
        """
        # 解析 URL
        parsed = urlparse(url)

        # 1. 处理 query 部分：先解码，再重新编码
        # unquote 会把 %2A 还原成 *，%20 还原成空格
        raw_query = unquote(parsed.query)

        # 2. 重新编码，safe='=&' 保证参数连接符不被编码
        encoded_query = quote(raw_query, safe='=&')

        # 重新组合
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            encoded_query,
            parsed.fragment
        ))
    def flush(self, url, params={} , wait_sec=2, headless=True):
        success = False
        cookies_dict = {}
        while not success:
            checkbox = self.page.ele('tag:input@type=checkbox', timeout=2)
            if checkbox and "id" not in checkbox.attrs:
                for _ in range(5):
                    try:
                        checkbox.click(by_js=True)
                        self.page.wait.load_start()
                        break
                    except Exception as e:
                        time.sleep(1)
            else:
                # if not params:
                #     url = self.safe_encode_url(url)
                #     self.page.get(url)
                # else:
                #     full_url = build_url_with_params(url, params)
                #     full_url = self.safe_encode_url(full_url)
                #     self.page.get(full_url)
                # full_url = "https://oatd.org/oatd/search?q=*:*%20AND%20pub_dt:%5B1801-01-01T00:00:00Z%20TO%201802-01-01T00:00:00Z%5D"
                # full_url ="https://oatd.org/oatd/search?q=a&form=basic"
                full_url = "https://oatd.org/oatd/search?q=%2A%3A%2A%20AND%20pub_dt%3A%5B2022-01-01T00%3A00%3A00Z%20TO%202023-01-01T00%3A00%3A00Z%5D"
                # full_url = 'https://oatd.org/'
                self.page.get(full_url)
                self.page.wait.load_start()
                if "Please slow down..." in self.page.html:
                    print(" cloudflare 已经通过")
                    self.page.refresh()
                elif self.page.ele("#facets") :
                    print("facets 已经加载成功")
                    self.page.refresh()
                else:
                    click_checkbox = None
                    self.page.activate_tab(1)
                    print("active tab 1")
                    self.page.refresh(ignore_cache=True)
                    self.page.wait.load_start()
                    for retry in range(5):
                        # 激活当前标签页
                        try:
                            self.page.wait.load_start()
                            x, y = pyautogui.locateCenterOnScreen('./screenshot-20260421-161129.png', confidence=0.8, region=(0, 0, 800, 600))
                            if x and y:
                                print(f"找到目标！中心坐标是：({x}, {y})")
                                pyautogui.click(x, y, duration= 1,button="LEFT" ,clicks = 2,)  # duration 模拟自然点击速度
                                pyautogui.moveTo(x, y, duration=0.5)  # 模拟鼠标移动到目标位置
                                pyautogui.mouseDown(x, y,button='left')
                                pyautogui.mouseUp(x, y,button='left')
                                # self.page.actions.move_to(x, y).click()  # 使用 DrissionPage 的 actions 模拟鼠标移动
                                print("点击并按住鼠标左键")
                                time.sleep(5)  # 按住1秒
                                break
                        except Exception as e:
                            print(f"未找到目标，重试 {retry}，错误：{str(e)}")
                            time.sleep(5)

                        self.page.wait.load_start()
                        checkbox = self.page.ele('tag:input@type=checkbox', timeout=2)
                        facets = self.page.ele("#facets")
                        print(f"facets :{ facets } \n checkbox :{ click_checkbox }")
                        if facets:
                            break
                        elif checkbox:
                            for idx in range(5):
                                try:
                                    checkbox.click(by_js=True)
                                    self.page.wait.eles_loaded("#facets")
                                    break
                                except Exception:
                                    print(f"点击 checkbox 失败，重试 {idx}")
                                    time.sleep(idx+2)
                            self.page.wait.load_start()
                            break
                        else:
                            self.page.wait.load_start() # 等待页面加载完成后再次检查 但是对js cloudfare 无效

                # DrissionPage 返回 cookies 列表，这里转成 dict
                cookies_list = self.page.cookies()  # list of dicts
                cookies_dict = {c.get('name'): c.get('value') for c in cookies_list if c.get('name')}
                success =  self.test_cookie(cookies_dict, full_url)
                print(f"cookie test :{ success }")
        return cookies_dict

    def test_cookie(self,cookies_dict, full_url):
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
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
        }
        # url = "https://oatd.org/oatd/search"
        params = {
        }

        if cookies_dict:
            for retry in range(3):
                try:
                    response = requests.get(full_url, headers=headers, cookies=cookies_dict, params=params,timeout=5)
                    if response and response.status_code == 200:
                        end_time = time.time()
                        print(f"success  when retry = {retry}  耗时 {end_time - start_time:.4f}s")
                        return True
                except Exception as e:
                    print(f"error timeout retry {retry}，{str(e)}")
                    time.sleep(5)
            else:
                return False
        return False

    def close(self):
        """关闭浏览器"""
        print("\n关闭浏览器...")
        self.page.close()
        print("浏览器已关闭")

if __name__ == "__main__":
    import requests
    cookies_flusher = CookieFlush(headless=False,port=9223)
    # flush_url = "https://oatd.org/oatd/search?q=%2A%3A%2A%20AND%20pub_dt%3A%5B1801-01-01T00%3A00%3A00Z%20TO%201802-01-01T00%3A00%3A00Z%5D"
    flush_url = "https://oatd.org"
    cookies_dict = cookies_flusher.flush(flush_url)
    print("获取到的 cookies：", cookies_dict)
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
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
    }
    url = "https://oatd.org/oatd/search"
    params = {
        "q": "*:* AND pub_dt:[1800-01-01T00:00:00Z TO 1801-01-01T00:00:00Z]"
    }
    if cookies_dict:
        for retry in range(10):
            response = requests.get(url, headers=headers, cookies=cookies_dict, params=params)
            # print(response.text)
            print(retry ,response.status_code)
            time.sleep(retry)


