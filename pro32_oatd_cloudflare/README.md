# oatd.org Cloudflare Turnstile 应对 — Cookie 刷新方案集

> 复现对象：`多探科技/pro4_oatd/`（cookie_flush 五方案 + spider 对接）· 技术分类：`waf` · 状态：✅ 离线部分可复现（13/13 通过）+ ⚠️ 真实 Cookie 刷新需浏览器与站点

## 站点与目标

- 站点：https://oatd.org（开放获取论文库）
- 加密参数：`cf_clearance` Cookie（Cloudflare Turnstile 验证后签发，绑定 IP+UA，约 30min~1h 有效）
- 目标接口：`GET /oatd/search?q=*:* AND pub_dt:[YYYY…TO YYYY…]&start=N`

## 技术要点

- 算法/保护类型：Cloudflare Turnstile 人机验证 + 频率管控（Cookie 类 WAF，无固定算法可还原，走浏览器自动化路线）
- 混淆情况：stealth.min.js（puppeteer-extra 反检测插件）+ 真实 Chrome CDP 外连（无自动化标记）
- 一句话概括：浏览器自动过 Turnstile 挑战 → 提取 cf_clearance → requests 侧携带继续爬取；挑战状态由 Turnstile DOM 状态机判别

## 逆向摘要

- 入口定位：请求出现 `403 + Just a moment...`（挑战页）→ 需刷新 Cookie；页面源码含 `cType: 'xxx'` 标记挑战类型
- 还原过程：
  1. **五方案演化**：pyautogui 截图识别（v1）→ DrissionPage DOM 状态机（v2）→ patchright 反检测（v3）→ **Playwright CDP 连接全新真实 Chrome**（v4，生产）→ Scrapling 库（v5，试验）
  2. 核心状态机：`none → loading → ready → verifying → solved`（Turnstile widget DOM 生命周期驱动），`slow_down` 独立态（验证已过但限速）
  3. 跨域 iframe 限制：checkbox 在 `challenges.cloudflare.com` iframe 内，JS 不可点，只能 bounding_box 定位 + 鼠标事件
  4. 拟人化：三次贝塞尔鼠标轨迹 + 中段微抖动 + 变速 + 点击前停顿
  5. Cookie 验证：requests 实测 200 才确认（不能只看 Cookie 存在）
- 主爬虫对接：60s 刷新节流 + `is_flushing` 多线程互斥 + 20 次重试（403 挑战→刷新 / Server Too Busy→指数退避）

## 复现

```bash
# 依赖: 仅标准库 (离线验证部分)
python main.py
```

- 样例输入 → 期望输出（内置 13 组合成用例，验证判定逻辑本身，非真实抓包）：

| 类别 | 组数 | 覆盖 |
|------|------|------|
| Turnstile 状态机判别 | 5 | ready / verifying / loading / slow_down / none（合成 HTML） |
| 挑战类型检测 | 5 | non-interactive / managed / interactive / embedded / 无 |
| 拟人贝塞尔轨迹 | 3 | 首尾精确、点数、相邻点距、零距退化、带抖动 |

## 验证与实测

- 样例对比：13/13 全部通过
- 真实请求验证：2026-04~05 生产运行（spider.py 用 v4 方案持续爬取 oatd 全年数据）；**真实 Cookie 刷新链路不在离线验证范围**，需本机 Chrome + 可访问 oatd.org 才能复现

## 备注

- 失效风险：Cloudflare 规则迭代快（Turnstile DOM/挑战类型可能改版），checkbox 坐标偏移等硬编码需定期校准；cf_clearance 有效期短需持续刷新
- 坑：headless 模式易被识别（生产用 `headless=False`）；"Please slow down..." 是验证通过但限速，勿误判为失败；UA 必须与浏览器侧一字不差
- 同目录文件：`cookie_flush*.py` ×5 为方案原码存档（v1~v5，依赖多探科技 util，仅作参考不直接运行）；`stealth.min.js` 为 puppeteer-extra 反检测插件提取版；`ANALYSIS.md` 为完整研究文档（机制剖析 + 8 条坑清单 + 方案选型）
