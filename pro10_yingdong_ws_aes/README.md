# 颍东先锋网 — 网盟 WAF：AES 会话加密 + WebSocket 指令渲染

> 复现对象：`spider research/其他/pro19 颍东先锋网 websocket/` · 技术分类：`encrypt` `waf` · 状态：✅ 可复现（8/8 通过，2026-06-29 实测）

## 站点与目标

- 站点：`https://www.ydxf.gov.cn/`（颍东先锋网，2026-06-29 实测）
- 防护：网盟 (WangMeng) **WEB_ISOLATION** WAF（openresty + Lua），appId 1748
- 加密参数：POST `/api/v1/sessions` 的 `{"data": 密文}` + 请求头 `etag`；内容经 WSS `wss://{域名}/{前缀}/pr/{token}/{b|c}/ws/{tabId}/{uuid}` 指令流渲染

## 技术要点

- 算法：**AES-128-CBC**（固定 key `0A234C4C639E015D` / 固定 IV `E08247708934F42E`）+ base64 `/`→`_` 变形 + **动态会话密钥派生**
- 保护类型：三层防护——资源加密前缀、Session AES 加密、WebSocket 二进制指令渲染（msgpack/JSON）
- 一句话概括：页面 HTML 是空壳，正文全靠服务端推指令重建 DOM——逆向核心是会话密钥派生链与指令协议

## 逆向摘要

- 入口定位：抓包见 `etag` + 加密 body → 从 `window.__wm__client_config__` 拿配置 → webpack bundle `app.3b14cce1.js` 中搜索 `createCipheriv` 定位 dynamicEncrypt
- 还原过程：
  1. 密钥派生链（**注意参数顺序**）：`enc1 = AES(e, 固定key, 固定iv)` 去 `_` 后取 `[1:17]` 得 **session_key**（作为 etag 头发送）；`enc2 = AES(session_key, 固定key, 固定iv)` 取 `[4:20]` 得 **priKey**
  2. session 请求体 = `AES(JSON, key=priKey, iv=session_key)`——**key/iv 与直觉相反**，且与派生链用的固定对不同
  3. 编码坑：`dynamicEncrypt` 输出 base64 后 `/`→`_`；派生 enc1 前还要 `.replace("_","")`（去掉所有下划线）再切片
  4. WSS 帧格式 `[seqNum, payload]`，服务端推送 `[[wrapper, [target, extra, command, ...args]]]`；CommandCodes 完整 47 项指令表已提取（31 NAVIGATE / 32 SYNC / 58 SIMPLE_HTML…）
  5. 直连门槛：Origin 头 + WIC token（~30 秒时效）+ 与浏览器一致的 tab_id；纯 Python 无法注册新 tab_id（工程方案用 Playwright）
- 数据来源：原项目 `ANALYSIS_REPORT.md`（含真实抓包 SYNC 帧 `[[-1,["","",32,1,false]]]`）

## 复现

```bash
pip install pycryptodome        # 唯一第三方依赖 (文本模式帧用 JSON, 无需 msgpack)
python main.py
```

| 验证项 | 结果 |
|--------|------|
| 密钥派生期望值 ×2（固定输入 → session_key / priKey） | ✅ |
| base64 `/`→`_` 变形往返 ×1 | ✅ |
| session 请求体往返 ×1（真实请求 JSON 结构，中文） | ✅ |
| 派生确定性 ×1 / WS 帧 NAVIGATE ×1 | ✅ |
| 真实 SYNC 帧 ×1（2026-06-29 观察）+ CommandCodes 抽查 ×1 | ✅ |

## 验证与实测

- 样例对比：8/8 通过；密钥派生期望值按 JS `genrandomString`/`hasKey` 流程逐值推导
- 真实请求验证：原项目 2026-06-29 WSS 直连成功（文本 `/c/` 与二进制 `/b/` 均可连，收到 SYNC 心跳）；Session POST 外部调用被 405（WAF 请求签名校验），浏览器内可成功

## 备注

- 失效风险：加密前缀 `1ywuKELSO2ahQuWZ` 与动态 Cookie 名随部署变化；token ~30 秒时效；新 tab_id 无法纯 Python 注册
- 坑：**etag 即 session_key**（服务器用 etag 重派生 priKey）；`/`→`_` 与派生切片顺序不可颠倒；session 加密 key=priKey/iv=session_key 与固定对相反
