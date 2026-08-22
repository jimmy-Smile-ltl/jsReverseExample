# 中国土地市场网 (landchina.com) 反调试分析报告

**日期**: 2026-06-30  
**URL**: `https://www.landchina.com/#/resultNotice?...`

---

## 一、总览

| 防护层 | 类型 | 有效性 | 影响范围 |
|--------|------|--------|----------|
| **CloudWAF (华为云)** | WAF — ⭐ 核心防护 | ✅ **强** | 保护 JS/CSS/API 全部资源 |
| disable-devtool v0.3.8 | 反调试库 | ⚠️ 仅影响浏览器 DevTools | 前端调试 |
| console.log 禁用 | 反调试 | ❌ 无关紧要 | 控制台输出 |
| Hash 头 | 签名 | ❌ 后端不校验 | 无 |
| Authorization | Token | ✅ 仅管理后台 | `/manage/*` 路由 |

**结论: 核心反爬是华为云 CloudWAF（行为画像 + IP 标记），非浏览器环境的请求会被逐步识别并封锁（418）。前端 JS 反调试为辅助手段。**

---

## 二、前端技术栈

- **框架**: Vue 2.x + Vue Router (hash mode)
- **UI 库**: Element UI
- **打包工具**: Webpack (code splitting)
- **地图**: 天地图 API v4.1.1 (TianDiTu)
- **WAF**: CloudWAF (来自阿里云/华为云? - 保护静态资源)

### JS 文件清单

| 文件 | 内容 |
|------|------|
| `chunk-vendors.6f217df8.js` | Vue + Element UI + **disable-devtool** + MD5 + axios |
| `app.093e01fb.js` | 主业务逻辑 + API 定义 + 路由 + 拦截器 |
| `310.6bbd4900.js` | `resultNotice` 页面组件（懒加载） |
| `tian-api.js` | 天地图地图库 |
| `vue.min.js` / `vue-router.min.js` | Vue 核心库 |

---

## 三、反调试机制详解

### 3.1 disable-devtool v0.3.8 (chunk-vendors.js)

`disable-devtool` 是一个开源的反调试库 (作者 theajack)，版本 `0.3.8`。

#### 检测方法

| 编号 | 类型 | 原理 |
|------|------|------|
| 0 | `RegToString` | 覆写 `RegExp.prototype.toString`，Firefox/QQ浏览器中测调用时间 |
| 1 | `DefineId` | 用 `__defineGetter__`/`Object.defineProperty` 给 div 的 `id` 设 getter 陷阱 |
| 2 | `Size` | 比较 `outerWidth` vs `innerWidth * devicePixelRatio`（DevTools 造成尺寸差异） |
| 3 | `DateToString` | 覆写 `Date.prototype.toString`，DevTools 会调用 ≥2 次 |
| 4 | `FuncToString` | 覆写 `Function.prototype.toString`，DevTools 会调用 ≥2 次 |
| 5 | `Debugger` | 插入 debugger 语句并测量执行时间（>100ms = DevTools 开了） |
| 6 | `Performance` | 比较 `console.log` vs `console.table` 在 50 元素大数组上的性能差异 |
| 7 | `DebugLib` | 检测 `window.eruda` 和 `window._vcOrigConsole` (vConsole) |

#### 轮询配置

```javascript
{
  interval: 500,           // 每 500ms 检测一次
  stopIntervalTime: 5000,  // 5 秒后自动停止轮询
  detectors: [0, 1, 3, 4, 5, 6, 7],  // 启用 7 种检测 (除 Size)
  clearLog: false,         // 不清除控制台
  disableMenu: false,      // 不禁用右键菜单
}
```

#### 检测到 DevTools 时的行为

```javascript
function onDevToolOpen() {
  // 优先: 跳转到 h.url（本站未配置）
  // 其次: 重写 HTML（本站未配置）
  // 兜底: 尝试 window.close() + history.back() 
  //       → 500ms 后跳转到 https://theajack.github.io/disable-devtool/404.html
}
```

**实际状态**: 本站未配置 `disable-devtool-auto` DOM 属性，且未找到全局 `disableDevtool` 对象。反调试库**可能未实际激活运行**（需进一步确认）。

### 3.2 console.log 禁用 (app.js)

```javascript
console.log = () => {}
```

在 app.js 初始化后，所有 `console.log` 输出被静默屏蔽。不影响 `console.warn`/`console.error`。

### 3.3 CloudWAF (华为云 WAF) — 核心反爬机制

#### 识别特征

- **Server 头**: `Server: CW` (CloudWAF)
- **Cookie**: `HWWAFSESID`、`HWWAFSESTIME` (Huawei WAF Session ID / Time)
- **拦截响应**: HTTP 418 + HTML 拦截页面
- **事件ID格式**: `{risk}-clou-{node}-{timestamp}-{hash}`
  - 低风险: `08-clou-37-xxx` (首次请求，低可疑度)
  - 高风险: `90-clou-37-xxx`、`90-clou-90-xxx` (行为画像触发)

#### 行为分析机制

CloudWAF 使用**渐进式行为画像**来识别爬虫：

```
请求 1 (curl): → 200 OK (WAF 未识别，放行 + 设置 HWWAFSESID)
请求 2 (curl, 带 cookie): → 418 BLOCK (检测到非浏览器 TLS 指纹)
请求 3 (Python requests): → 418 BLOCK (IP 风险评分已升高)
请求 N (任何非浏览器): → 418 BLOCK (IP 已被标记为高危)
```

**关键发现**:
1. **WAF 保护范围**: `api.landchina.com` 和 `www.landchina.com` 的静态资源都受保护
2. **IP 级别封锁**: 一旦 IP 被标记为 bot，所有后续请求（无论什么工具）都返回 418
3. **TLS 指纹检测**: 直接 curl（OpenSSL）、Python requests（Python ssl）的 TLS 指纹与真实浏览器不同
4. **CORS 伪装**: 浏览器中的 CORS 错误实为 WAF 拦截 — WAF 返回的 418 HTML 页面缺少 CORS 头，浏览器将其解释为 CORS 错误
5. **首次请求可能成功**: WAF 首次会给"善意推定"，但 2-3 次请求后即封锁

#### 真实浏览器行为验证

在 CloakBrowser 中，从 `www.landchina.com` 到 `api.landchina.com` 的跨域 XHR 也全部失败（CORS/418）。这进一步证实：
- 网页的 API 调用依赖于 WAF 放行 CORS 预检请求
- 当 WAF 不信任浏览器会话时，连真实网页的数据加载也会被阻断

#### 绕过方向

| 方案 | 可行性 | 说明 |
|------|--------|------|
| **curl_cffi + 住宅代理** | ⭐⭐⭐ | 浏览器 TLS 指纹 + IP 轮换避免标记 |
| **Playwright + 代理池** | ⭐⭐⭐ | 真实浏览器环境，WAF 无法区分 |
| **IP 代理轮换** | ⭐⭐ | 需要频繁切换 IP，成本较高 |
| **Python requests 直连** | ❌ | IP 会被快速标记 |
| **curl 直连** | ❌ | 同上，即使带 WAF Cookie 也不行 |

---

## 四、API 接口分析

### 4.1 基础信息

- **Base URL**: `https://api.landchina.com`
- **请求方式**: POST（大部分）/ GET（少量）
- **认证**: 数据查询无需认证，管理后台需要 Bearer Token
- **Hash 头**: `MD5(userAgent + dayOfMonth + URL最后一段)` ← **后端不校验**
- **WAF 防护**: ⚠️ **华为云 CloudWAF 保护** — 非浏览器请求会被 418 拦截

### 4.2 核心 API: 供地结果列表

```
POST https://api.landchina.com/tGdxm/result/list
Content-Type: application/json
Hash: <MD5>  ← 可选，后端不校验
```

**⚠️ 此 API 受 CloudWAF 保护**，直接 Python requests / curl 调用会被 418 拦截。需要 TLS 指纹伪装或使用真实浏览器。

#### 请求参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `pageNum` | int | 页码，从 1 开始 |
| `pageSize` | int | 每页条数 |
| `xzqDm` | string | 行政区代码（6位数字，如 `"320505"`）|
| `gyFs` | string | 供应方式（如 `"挂牌出让"`、`"划拨"`、`"协议出让"`）|
| `tdYt` | string | 土地用途 |
| `startDate` | string | 开始日期 `"YYYY-MM-DD 00:00:00"` |
| `endDate` | string | 结束日期 `"YYYY-MM-DD 23:59:59"` |
| `dzBaBh` | string | 电子监管号 |
| `tdZl` | string | 土地坐落（关键词搜索）|

#### 响应格式

```json
{
  "msg": "操作成功",
  "code": 200,
  "data": {
    "total": 512,
    "list": [{
      "gdGuid": "01af4c8ece8b4f1daa901eb0e8c5cede",
      "xzqDm": "320505",
      "xzqFullName": "江苏省苏州市虎丘区",
      "tdZl": "浔阳江路以东...",
      "gyFs": "协议出让",
      "gyMj": 0.1022,
      "tdYt": "一类工业用地",
      "qdRq": "2026-06-01T12:06:00"
    }],
    "pageNum": 1,
    "pageSize": 10,
    "pages": 52
  }
}
```

### 4.3 其他有用 API

| 端点 | 说明 |
|------|------|
| `POST /bptFieldEnum/xzq` | 获取行政区划树 |
| `GET /bptFieldEnum/keyCity` | 获取重点城市列表 |
| `POST /bptFieldEnum/tdytTreeList` | 获取土地用途分类树 |
| `POST /tGdxm/result/detail` | 供地结果详情（参数 `gdGuid`）|
| `POST /tGygg/transfer/list` | 土地供应公告列表 |
| `GET /tGygg/index/supplyCount` | 土地供应统计数 |

### 4.4 前端限制

- 前端分页组件限制显示 **6000 条**（`total > 6000` 时截断）
- API 本身没有总量限制，可通过分页遍历全部数据
- 建议按天分片，每片数据量约 500-2000 条

---

## 五、Hash 签名算法

虽然后端不校验，但前端确实生成了 Hash 头：

```javascript
// app.js 请求拦截器
let a = require(2966);  // MD5 模块
let r = e.url.split("/");
t["Hash"] = a(navigator.userAgent + (new Date).getDate() + r[r.length - 1]);
```

### 算法公式

```
Hash = MD5(userAgent + dayOfMonth + lastPathSegment)
```

### 示例

```
输入: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36..." + "30" + "tGdxm/result/list"
输出: "c9bf226a0ac715a9aa3e54a5635219b4"
```

**注意**: `dayOfMonth` 是 `new Date().getDate()` 返回的数字（1-31），无前导零。

---

## 六、爬虫策略建议

### 6.1 核心挑战: CloudWAF IP 封锁

华为云 CloudWAF 使用**行为画像 + IP 级别封锁**:
1. 非浏览器 TLS 指纹 → 首次可能放行，2-3次后标记 IP
2. 一旦 IP 被标记 → 所有请求 418 拦截
3. 封锁是 IP 维度的（非 session），换工具也无效

### 6.2 方案 A: curl_cffi + 代理轮换（推荐）

```python
import hashlib
from curl_cffi import requests as cffi_requests

class LandchinaSpider:
    def __init__(self):
        self.ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/146.0.0.0 Safari/537.36"
        )
        self.base_url = "https://api.landchina.com"

    def _gen_hash(self, path):
        from datetime import datetime
        day = datetime.now().day
        last_seg = path.split("/")[-1]
        return hashlib.md5(f"{self.ua}{day}{last_seg}".encode()).hexdigest()

    def fetch_results(self, start_date, end_date, page=1, page_size=50, proxy=None):
        url = f"{self.base_url}/tGdxm/result/list"
        headers = {
            "Content-Type": "application/json",
            "Hash": self._gen_hash("tGdxm/result/list"),
            "User-Agent": self.ua,
            "Origin": "https://www.landchina.com",
            "Referer": "https://www.landchina.com/",
            "Accept": "application/json, text/plain, */*",
        }
        payload = {
            "pageNum": page,
            "pageSize": page_size,
            "startDate": f"{start_date} 00:00:00",
            "endDate": f"{end_date} 23:59:59",
        }
        proxies = {"http": proxy, "https": proxy} if proxy else None
        resp = cffi_requests.post(
            url, json=payload, headers=headers,
            proxies=proxies, impersonate="chrome120"
        )
        if resp.status_code == 418:
            raise Exception(f"WAF blocked IP, need proxy rotation")
        return resp.json()
```

### 6.3 方案 B: Playwright 浏览器自动化

```python
from playwright.sync_api import sync_playwright

def fetch_via_browser(start_date, end_date, proxy=None):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            proxy={"server": proxy} if proxy else None
        )
        page = browser.new_page()
        # 先访问主站建立 WAF 信任
        page.goto("https://www.landchina.com/", wait_until="networkidle")

        # 通过页面内 JS 调用 API
        result = page.evaluate("""
            async (params) => {
                const resp = await fetch(
                    'https://api.landchina.com/tGdxm/result/list', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(params)
                });
                return await resp.json();
            }
        """, {
            "pageNum": 1, "pageSize": 10,
            "startDate": f"{start_date} 00:00:00",
            "endDate": f"{end_date} 23:59:59"
        })
        browser.close()
        return result
```

### 6.4 方案 C: 利用首次 WAF 宽容窗口

观察到的规律: 新 IP 的首次 API 请求会被 WAF 放行。可以:
```python
# 每次使用新代理发起首次请求
# 每次请求都切换代理 IP
# 保持低频（1-2 req/s），避免触发行为分析
```

### 6.5 注意事项

1. **按天分片**: 每天数据量 500-2000 条，按天查询避免 6000 条截断
2. **代理质量**: 需要住宅代理，数据中心 IP 更容易被标记
3. **请求频率**: 控制频率避免触发频率限制（建议 1-2 req/s）
4. **Hash 生成**: 虽不校验，建议保持以应对未来更新
5. **反调试**: 用 API 直连 + 代理方案后，完全不需要关心前端反调试
6. **WAF 封锁恢复**: 被封锁的 IP 可能需要数小时才能恢复

---

## 七、URL 中 `[object Object]` 参数问题

原始 URL 中 `xzq=%5Bobject%20Object%5D` 是 Vue Router 的一个常见 bug：

```javascript
// resultNotice 组件的 activated() 钩子
this.formInline.xzq = this.$route.query.xzq || void 0
```

当上一个页面通过 `$router.push({ query: { xzq: someObject } })` 传递复杂对象时，Vue Router 会调用 `.toString()` 序列化，产生字面量 `"[object Object]"`。

在 `_resultList` 方法中:
```javascript
t = "string" == typeof this.formInline.xzq
    ? this.formInline.xzq  // ← "[object Object]" 被当作字符串传给 API
    : this.formInline.xzq ? this.formInline.xzq[this.formInline.xzq.length - 1] : void 0
```

**影响**: 当 URL 中 xzq 为 `[object Object]` 时，API 收到无效的 `xzqDm` 值，但不影响查询（后端忽略无效值）。直接通过 API 爬取时不存在此问题。

---

## 八、CloudWAF 详细分析

### WAF 类型确认

| 特征 | 值 | 说明 |
|------|-----|------|
| Server 头 | `CW` | CloudWAF |
| Session Cookie | `HWWAFSESID` | Huawei WAF Session ID |
| Time Cookie | `HWWAFSESTIME` | Session timestamp |
| 拦截状态码 | `418` | I'm a teapot (WAF 常用) |
| Event ID 格式 | `{risk}-clou-{node}-{ts}-{hash}` | 风险评分格式 |

### 风险评分演变

```
阶段 1 (首次请求):
  Event ID: 08-clou-37-20260630113906-0e7e24ae  (risk=08, 低风险)
  结果: 200 OK ✅

阶段 2 (行为画像触发):
  Event ID: 90-clou-37-20260630114420-14fb04d0  (risk=90, 高风险)
  结果: 418 BLOCK ❌

阶段 3 (IP 标记):
  Event ID: 90-clou-90-20260630114421-587848b4  (node=90, risk=90, 确认封锁)
  结果: 418 BLOCK ❌
```

### WAF 检测维度（推测）

1. **TLS 指纹**: JA3/JA4 指纹不在白名单内
2. **HTTP/2 帧序列**: 浏览器有特定的 HTTP/2 优先级帧序列
3. **Header 顺序**: 浏览器 Headers 有固定顺序（:method, :authority, :scheme, :path 等）
4. **Cookie 一致性**: 是否携带并回传 WAF 会话 Cookie
5. **CORS 预检**: OPTIONS 请求的处理方式
6. **行为频率**: 请求间隔、并发连接数

---

## 九、附录

### A. 反调试库版本

- 名称: `disable-devtool`
- 版本: `0.3.8`
- GitHub: https://github.com/theajack/disable-devtool
- 开源协议: MIT

### B. 检测到的全局变量

- `webpackChunknew_landchina_frontend` — Webpack chunk 加载器
- `__core-js_shared__` — core-js polyfill

### C. 浏览器 User-Agent (CloakBrowser)

```
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36
```

### D. 已验证的 API 响应 (2026-06-01, 首次请求)

```json
{
  "msg": "操作成功",
  "code": 200,
  "data": {
    "total": 512,
    "pageNum": 1,
    "pageSize": 10,
    "pages": 52,
    "list": [
      {"xzqFullName": "江苏省苏州市虎丘区", "gyFs": "协议出让", "gyMj": 0.1022},
      {"xzqFullName": "浙江省绍兴市诸暨市", "gyFs": "挂牌出让", "gyMj": 0.66649},
      {"xzqFullName": "广东省肇庆市四会市", "gyFs": "划拨", "gyMj": 0.011048}
    ]
  }
}
```

### E. 供应方式枚举

从 API 返回中观察到的供应方式: `"协议出让"`, `"挂牌出让"`, `"划拨"`, 可能还有 `"拍卖出让"`, `"招标出让"`, `"租赁"` 等。

### F. 用途分类示例

`"一类工业用地"`, `"二类工业用地"`, `"公路用地"`, `"公园绿地"`, `"城镇村道路用地"`, `"消防用地"`, `"供电用地"`
