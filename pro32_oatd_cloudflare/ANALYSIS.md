# pro4_oatd — Cloudflare Cookie 刷新应对措施研究

> 研究对象：`多探科技/pro4_oatd/`（oatd.org 开放获取论文库爬虫）
> 研究日期：2026-08-29 · 状态：生产运行中（spider.py / spider_list.py 使用 `cookie_flush_playwright_cdp.py`）

## 1. 站点与防护形态

| 项 | 内容 |
|----|------|
| 站点 | https://oatd.org（Open Access Theses and Dissertations，开放获取论文库） |
| 防护 | Cloudflare（含 Turnstile 人机验证 + 频率管控） |
| 数据接口 | `GET /oatd/search?q=*:* AND pub_dt:[YYYY-01-01T00:00:00Z TO YYYY-01-01T00:00:00Z]&start=N`（按年分片翻页） |
| 成功判定 | HTTP 200 且响应含 `Search Limiters` |

**三种异常响应**（spider.py 重试循环内区分处理）：

| 响应特征 | 含义 | 应对 |
|---------|------|------|
| 403 + `Just a moment...` | Cloudflare Turnstile 挑战页 | 触发 Cookie 刷新 |
| 200 + `Server Too Busy - Please slow down` | 频率管控（非挑战失败） | 指数退避 `sleep(5 * retry)` |
| 其他（无 Search Limiters） | 参数/被拦等异常 | 继续重试 |

## 2. Cloudflare 挑战机制速览（本项目的认知模型）

1. **cf_clearance Cookie**：通过 Turnstile 验证后签发，绑定 **IP + User-Agent**，有效期约 30min~1h。requests 侧必须携带与浏览器一致的 UA（本项目 Chrome 147 / Linux），否则 Cookie 失效。
2. **挑战类型 cType 三型**（页面源码含 `cType: 'xxx'`）：
   - `non-interactive`：后台自动验证（环境评分足够），无需点击，等待通过即可
   - `managed`：CF 托管验证
   - `interactive`：必须点击 Turnstile checkbox（本项目常见形态）
   - 另有 `embedded`（页面直接嵌入 turnstile iframe，无 cType 标记）
3. **跨域 iframe 限制**：Turnstile widget 在 `challenges.cloudflare.com` 域 iframe 内，页面 JS 无法访问其内部 DOM —— 只能通过 iframe 元素的 bounding_box 定位坐标，用鼠标事件点击（无法 `ele.click()` 直接命中）。
4. **"Please slow down..." ≠ 失败**：页面出现该文案说明验证已通过，但请求频率被 CF 降速管控 —— 判断逻辑必须区分「验证状态」与「限速状态」。

## 3. 五个 CookieFlush 方案演化

按开发时间顺序，是「截图识别 → DOM 状态机 → 反检测引擎 → 真实浏览器 → 现成库」的完整演化链：

| 版本 | 文件 | 引擎 | 点击方式 | 问题/局限 |
|------|------|------|---------|-----------|
| v1 | `cookie_flush.py` | DrissionPage ChromiumPage | `click(by_js=True)` + **pyautogui 截图识别 checkbox**（`locateCenterOnScreen` confidence=0.8）+ OS 级鼠标 | 截图识别脆弱（分辨率/缩放敏感）；by_js 点击易被 CF 风控识别为自动化 |
| v2 | `cookie_flush_drissionPage.py` | DrissionPage | **Turnstile DOM 状态机** + `actions.move_to/click` 拟人点击 | DrissionPage 指纹特征与主流自动化工具不同，但有自身检测面 |
| v3 | `cookie_flush_playwright.py` | **patchright**（Playwright 反检测分支）launch 模式 | 状态机 + 拟人点击 | 打包浏览器仍有部分自动化标记 |
| v4 | `cookie_flush_playwright_cdp.py` ⭐生产 | **Playwright CDP 连接全新真实 Chrome**（每次独立 user-data-dir + 空闲端口） | 状态机 + **贝塞尔曲线人类轨迹** + 拟人点击 | 最稳；需本机有 Chrome |
| v5 | `cookie_flush_scrapling.py` | Scrapling 库 StealthyFetcher | 库内置 `solve_cloudflare=True` | 依赖第三方库对 CF 的持续适配，不可控 |

**选型结论**：v4 为生产方案 —— 真实 Chrome 进程无 `navigator.webdriver` 等自动化标记（`--disable-blink-features=AutomationControlled` + CDP 外连），指纹最接近真人。

## 4. 生产方案（v4）机制剖析

### 4.1 浏览器生命周期
```
_start_chrome(): tempfile.mkdtemp 独立 user-data-dir（每次全新身份）
               + 空闲端口探测（socket bind，优先用户指定 9223，备选 9700-9799）
               + 一整套去特征启动参数（--no-sandbox/--disable-blink-features=AutomationControlled/
                 --no-first-run/--disable-extensions/--metrics-recording-only 等 20+ 项）
               + CDP 就绪轮询（/json/version，20×0.5s）
_start_browser(): playwright.chromium.connect_over_cdp(cdp_url)   # 外连，非 launch
                + new_context(UA=Chrome147 Linux)                  # 独立隐身 context
                + CDP Page.addScriptToEvaluateOnNewDocument 注入 stealth.min.js
```
> `stealth.min.js` 为 puppeteer-extra `extract-stealth-evasions` 生成（180KB，2026-05-11），随文档在项目目录。

### 4.2 Turnstile 状态机（核心）
`_ts_state()` 用 `page.evaluate` 从**主页面视角**查询 DOM，状态枚举：
```
none → loading → ready → verifying → solved
          ↑ widget 未渲染    ↑ 点击后 spinner 可见   ↑ widget 从 DOM 消失
```
- 检测特征：`iframe[src*=challenges.cloudflare.com/cdn-cgi/challenge-platform]`、`#cf-turnstile`、spinner 选择器、标题 `Just a moment`
- `slow_down` 独立状态（body 含 `Please slow down` / `Server Too Busy`）
- 状态机轮询 `_wait_for_ts_state(targets, timeout)`：0.5s 间隔
- 挑战流程：`non-interactive` → 等 solved（≤90s）；否则定位 checkbox → 拟人点击 → 等 solved（≤120s）→ 未过则递归重试

### 4.3 拟人化（`_human_mouse_move` / `_human_click`）
```
三次贝塞尔曲线轨迹（控制点带随机偏移 uniform(-80,80)）
+ 中段微抖动 uniform(-1.5,1.5)
+ 变速（两端慢中间快: delay = 0.003 + 0.012*(1-|2p-1|)）
+ 点击 = 移到附近(±5px) → 停顿 0.08~0.2s → 精确移入 → 停顿 → down → 0.04~0.1s → up
+ 鼠标坐标跨页面记忆（_mouse_x/_mouse_y 从实例随机初始化）
```

### 4.4 Cookie 提取与验证（`flush()`）
```
导航目标页 → 状态机判断 → 有挑战则 _solve_cloudflare()
→ #facets/#ticker 加载或 "Please slow down..." 均视为就绪
→ 5 轮等待（wait_sec + retry*3）逐轮 context.cookies() 提取
→ test_cookie(): requests 实测 200（3 次重试、5s 间隔）
```

## 5. 主爬虫对接架构（spider.py / spider_list.py）

```
SpiderOATD.__init__: CookieFlush(port=9223, headless=False)  # 有头！headless 易被 CF 识别
                     self.cookies 预置一枚历史 cf_clearance 兜底
                     is_flushing=False / flush_time=0 / global_lock

flush_cookies(url):  [全局锁保护]
  60 秒节流（<60s 或 is_flushing → 其他线程 wait 循环 2s 轮询）
  → cookie_flusher.flush(url) → cookies.update → flush_time 刷新

search_one_page(page_url): [每页 20 次重试]
  200 + "Search Limiters"            → 成功返回
  "Server Too Busy"                  → sleep(5*retry) 指数退避
  403 + "Just a moment..."           → 锁内 flush_cookies → sleep(2) → continue
```

**设计要点**：
- **刷新节流 + 互斥**：多线程并发遇到 403 时只有一个线程真正刷新，其余等待 —— 防止「10 个线程同时刷 cookie」触发更严风控
- **UA 一致性**：cookie_flush 与 requests 使用完全相同的 headers（含全套 sec-ch-ua/sec-fetch），cf_clearance 与 UA 绑定
- **分年分片**：1800~今按年遍历，天然控制频率；每页 retry 上限 20

## 6. 关键坑清单（实战沉淀）

| # | 坑 | 说明/解法 |
|---|----|----------|
| 1 | **headless 被识别** | 最终 `headless=False` 有头运行（Linux 服务器需要 X 或 xvfb） |
| 2 | **跨域 iframe 不可 JS 点击** | checkbox 在 challenge iframe 内，只能 `frame_element().bounding_box()` 拿坐标 + 鼠标事件 |
| 3 | **"Please slow down..." 误判为失败** | 该文案 = 验证已过但被限速；需与 403 挑战页区分 |
| 4 | **Cookie 与 UA/IP 绑定** | 浏览器与 requests 的 UA 必须一字不差（Chrome 147 Linux 全套 headers） |
| 5 | **频繁刷新触发升级风控** | 60s 节流 + 多线程互斥；宁可重试等待不重复刷新 |
| 6 | **pyautogui 截图识别不可靠** | 分辨率/缩放/主题变化即失效，v2 起废弃，改 DOM 状态机 |
| 7 | **cf_clearance 过期静默失效** | test_cookie 用 requests 实测 200 才确认；纯看 Cookie 存在不保险 |
| 8 | **状态机卡在 loading** | widget 渲染慢；`loading→ready` 等待放宽 20~30s，且「CF iframe 存在但状态 none」时强制按 ready 处理（drissionPage 版的经验） |

## 7. 与仓库其他 WAF 方案的关系

| 项目 | 防护 | 应对路线 |
|------|------|---------|
| 本项目 oatd | Cloudflare Turnstile | 浏览器自动化过验证 + cf_clearance 刷新（**本报告**） |
| jsReverseExample/pro01 | 加速乐 521 | 双层 JS 挑战 Cookie hook + SHA 暴力破解（纯算法） |
| jsReverseExample/pro03 | 阿里云 WAF acw_sc__v2 | 固定置换表 unsbox + 固定 key XOR（纯算法） |
| ruishuExample/ | 瑞数 WAF | sdenv 补环境 / 浏览器三档决策 |
| 多探科技/pro30 | AWS WAF | `aws-waf-token 逆向.md`（纯算法 token 生成） |

**路线选择判断**：Cookie 类 WAF（Cloudflare/Akamai）的验证是「会话评分 + 浏览器行为」，无固定算法可还原 → 走**浏览器自动化刷新**路线；而加速乐/阿里云 WAF/瑞数有确定性的 JS 挑战算法 → 走**纯算法还原**路线。

## 8. 待改进建议

1. `flush_cookies` 的互斥等待循环若 flushing 线程异常退出未复位 `is_flushing`，其余线程会死等 —— 建议 try/finally 复位或超时熔断
2. 方案 v5（scrapling）可作备胎：库更新快，值得定期对比测试
3. `_locate_turnstile_checkbox` 的坐标 `randint(26,28)` 硬编码基于 widget 尺寸假设，CF 改版后需重新校准 —— 建议做成相对 bounding_box 的比例偏移
