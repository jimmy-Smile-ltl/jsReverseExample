# 南方航空 机票搜索 — encryptArgs 绕过方案与请求参数关系

> 复现对象：`spider research/机票/pro4 南方航空/auto_version/` · 技术分类：`encrypt env` · 状态：🔒 仅样例（加密未逆向，仅复现可验证的参数关系）

## 站点与目标

- 站点：https://global.csair.com（南航国际站机票搜索）
- 加密参数：请求体经 **RSA+RC4 加密 + encryptArgs 令牌**；搜索参数从 Vuex `state.execution.info` 提取（含 `execution` 32 位 hex 令牌）
- 目标接口：`POST /api/shop/app`（主搜索）、`POST /api/shop/decryptArgs`（解密参数）、`GET /api/shop/next/{id}`（分页）

## 技术要点

- 算法/保护类型：AWS CloudFront WAF（检测无头浏览器）+ 请求体 RSA+RC4 加密 + `encryptArgs` 一次性令牌
- 混淆情况：前端 webpack 打包，加密逻辑未深入
- 一句话概括：**未做 crypto 逆向**——用隐身浏览器在真实页面完成搜索，从 Vuex store 直接窃取合法加密参数；抓包中可确定性验证的关系是 `requestId = base64url("sliceGrid:B2C_SEARCH_{dep}-{arr}_{date}_{execution}")`

## 逆向摘要

- 入口定位：Playwright + stealth.js 加载真实页面 → 页面内发起搜索 → 通过 Vuex store 注入的 hook 提取 `state.execution.info`（含 dep/arr/date/execution 及 encryptArgs）
- 还原过程：
  1. 抓包 `test_oneway.json` 等 3 组请求，发现 `searchParams.execution` 与 `requestId` 共享同一 32 位 hex 令牌
  2. 解码 requestId 确认模板：`sliceGrid:B2C_SEARCH_{dep}-{arr}_{date}_{execution}`（base64url 无 padding）
  3. execution 由服务端派生（与 /api/shop/app 的请求参数绑定，含时间/会话因子），算法未逆向
  4. main.py 仅复现该确定性模板关系（build + parse 双向验证）
- 绕过要点：CloudFront 对无头浏览器指纹敏感 → playwright-stealth 补 `webdriver`/`navigator.plugins` 等；crypto 层被真实浏览器原生完成，无需还原

## 复现

```bash
# 依赖: 仅标准库 (base64)
python main.py
```

- 样例输入 → 期望输出（内置在 `SAMPLE_CASES`，3 组，2026-06 抓包）：

| 输入（dep/arr/date/execution） | 期望输出（requestId） |
|------|---------|
| LAX/CAN/2026-06-10/`78080ec6...8245` | `c2xpY2VHcmlkOkIyQ19TRUFSQ0hfTEFYLUNBTl8yMDI2LTA2LTEwXzc4MDgwZWM2NjM4NTQzYjg4MWI5ZDJhZGUyZWQ4MjQ1` |
| LAX/CAN/2026-06-10/`9c8ed616...3907` | `c2xpY2VHcmlkOkIyQ19TRUFSQ0hfTEFYLUNBTl8yMDI2LTA2LTEwXzljOGVkNjE2Y2FlNmY0NDQ4M2U3Nzg4OGI1ZGIzOTA3` |
| LAX/CAN/2026-06-10/`3886d69e...4207` | `c2xpY2VHcmlkOkIyQ19TRUFSQ0hfTEFYLUNBTl8yMDI2LTA2LTEwXzM4ODZkNjllZjc2OWI3MzEzMTg0ZTI3MTUwYTQ0MjA3` |

## 验证与实测

- 样例对比：3/3 全部通过（含 requestId 反向解析出 execution 的校验）
- 真实请求验证：2026-06 南航官网隐身浏览器实测搜索成功（原项目 `logs/` 有运行记录）；crypto 加密本身未复现

## 备注

- 失效风险：encryptArgs 为一次性令牌、execution 有有效期，绕过方案依赖真实浏览器环境；CloudFront 规则可能更新
- 坑：CloudFront 检测无头浏览器（缺 `playwright-stealth` 时直接拦截）；Vuex 状态需在搜索完成后同步提取，否则 execution 为空
- 如需完整还原：从 `POST /api/shop/app` 请求体加密入手（RSA 公钥 + RC4 会话密钥链），工作量较大，未执行
