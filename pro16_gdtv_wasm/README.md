# 荔枝网 gdtv.cn — WASM API 认证：扣 webpack chunk 5 + 5 补丁补环境

> 复现对象：`spider research/其他/pro15 荔枝网 wasm/` · 技术分类：`wasm` + `env` · 状态：✅ 可复现（11/11 通过，2026-08-19 验证）

## 站点与目标

- 站点：`https://www.gdtv.cn/`（广东广播电视台荔枝网，原项目 2026-06-21 实测）
- 加密参数：请求头 `x-itouchtv-ca-signature` / `x-itouchtv-ca-timestamp` / `x-itouchtv-ca-key` / `x-itouchtv-client` / `x-itouchtv-device-id`；未认证返回 401 `Unauthorized access!`
- 目标接口：`GET https://gdtv-api.gdtv.cn/api/v1/seoConfig` → 200（原项目另验证 hotnews/rollNews/channel 3 端点）

## 技术要点

- 算法：**Rust + wasm-bindgen**（512KB WASM 以 base64 data URI 内嵌在 698KB webpack chunk 5 `vendor_w.js`），导出 `a()` 生成认证 headers，**时间戳为唯一随机源**
- 保护类型：WASM 保护 + 环境检测（`typeof global` 探测 Node）+ webpack 代码分割（chunk 按需加载）
- 一句话概括：不跑完整前端——**拦截 webpackJsonp 只注册 module 266 + 假 webpack 运行时**，5 个补丁让 WASM 走浏览器分支

## 逆向摘要

- 入口定位：XHR 断点搜 `x-itouchtv-ca-signature` → `S()` header 构建器（client.js）→ `m()` WASM 桥（chunk-libs.js）→ `n.e(5)` 加载 chunk 5 → module 266 `B.a()`
- 还原过程：
  1. **参数格式是关键**：`B.a(METHOD, FULL_URL, deviceId, "WEB_PC", "", undefined)`——第 1 参是 HTTP 方法，第 2 参是完整 URL（原项目在此踩坑 2 天）
  2. 扣代码：正则提取 base64 WASM → 假 webpack 运行时 + `webpackJsonp.push` 拦截 → stub module 43/147（Redux 工具）→ `eval(vendorCode)` + `B.initSync(wasmBytes)`
  3. **5 个补丁**：`delete globalThis.global`（WASM 用 `typeof global` 检测 Node）、`Window` 构造、`Location.prototype`、`document`、正确的 `B.a` 参数
  4. 30 个 wbg 导入（`__wbg_getTime`/`__wbg_getTimezoneOffset`/`__wbg_instanceof_Window` 等）由 vendor 内部 `t()` 自动生成
  5. 时间戳处理：微秒→自定义纪元（减 62135683200000）→ 加时区偏移×1000；签名内嵌时区偏移
  6. **固定时间戳实验**（`verify_fixed.js` 覆写 `Date.getTime`/`Date.now`/`getTimezoneOffset`）：URL 与 method 参与签名；**deviceId 不参与**（仅 header 回显）

## 复现

```bash
# 依赖: node.js (WASM 必需) + Python 标准库 (0 第三方)
python main.py            # 结构/确定性/参与项 11 项验证
python main.py --live     # 追加真实请求验证 (需网络)
```

| 验证项 | 结果 |
|--------|------|
| 固定时间戳期望值 ×3（案例 1 与真实 cli.js 抓包逐位一致） | ✅ |
| 确定性 ×1 / deviceId 不参与签名 ×1 / 随机时间戳非确定性 ×1 | ✅ |
| 时间戳贴近当前时间 ×1 / 签名 44 字符 base64→32B ×1 / 6 headers 结构 ×1 | ✅ |
| vendor_w.js 完整 ×1 / 内嵌 WASM 提取 511,963B ×1 / 5 补丁源码检查 ×1 | ✅ |

## 验证与实测

- 样例对比：11/11 通过；固定时间戳期望值前缀（`60d/Glg/...`）与 2026-08-19 真实 cli.js 输出逐位一致
- 真实请求验证：原项目 2026-06-21 端到端 4/4（签名生成/HTTP/参数/稳定性）；`python main.py --live` 可现场复测

## 备注

- 失效风险：`vendor_w_b4fcb8bf.js` 文件名带 hash，前端发版需重新提取；`x-itouchtv-ca-key` 常量（89541943007407288657755311868534）可能更换；签名含时区偏移（verify_fixed.js 已固定 UTC+8 保证跨机器）
- 坑：参数格式（method+fullUrl）错误直接 `unreachable`；`delete globalThis.global` 是隐藏 Node 的关键补丁；deviceId 只回显不签名，重复用固定值即可；Node v24+ 的 getter-only `navigator` 需 try-catch 兜底
