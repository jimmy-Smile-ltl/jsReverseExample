# 米画师 — WASM 签名：8 补丁补环境 + Rust wasm-bindgen 模块

> 复现对象：`spider research/其他/pro14 米画师 wasm/` · 技术分类：`wasm` + `env` · 状态：✅ 可复现（11/11 通过，2026-08-19 验证）

## 站点与目标

- 站点：`https://www.mihuashi.com/artworks`（约稿平台，原项目 2026-06-21 实测）
- 加密参数：请求头 `M-S`（签名）/ `M-T`（时间戳）/ `Web-Version: frontend`；签名错误返回 403 `{"error":"signature invalid"}`
- 目标接口：`GET /api/v1/artworks/search?page=1&type=recent` → 200 + `total_pages`

## 技术要点

- 算法：**Rust + wasm-bindgen 编译的 64KB WASM**（`mhs_fe_sign_bg.wasm`），内嵌浏览器指纹（favicon href + navigator）+ 32B 随机 nonce，输出 base64url 变体（`_` 与 `/` 共存、无 `=`）
- 保护类型：WASM 保护 + 环境检测（`instanceof Window` / `process`/`require` 探测）+ **服务端 UA 校验**
- 一句话概括：反编译还原公式不可行——**补 8 个环境补丁直接运行原始 WASM**，固定 nonce 时浏览器与 Node 输出字节级一致

## 逆向摘要

- 入口定位：XHR 断点搜 `M-S` header → 拦截器 `http.B6ZEV3BE.js` 的 `G` 函数（139 行）→ WASM 加载器 `http.NcR9CHD7.js` 的 `pe` 类
- 还原过程：
  1. 签名输入 = `encodeURI(e.url)` **只取 PATH**；带 query 会 403（签名 124≠100 字符，长度与 PATH 正相关：28 字符 PATH→100 字符签名）
  2. **UA 服务端校验**：HTTP header 必须等于签名内嵌的 `navigator.userAgent`（`run_sign.js` 第 86 行）
  3. WASM 用 `Reflect.get(global)` 遍历探测 Node 特征 → 构造**干净 browserGlobal**（只含 crypto/document/navigator/location，不含 process/Buffer/require）
  4. 8 个补丁：`Window` 构造函数、`instanceof_Window→1`、`accessor_PROCESS→0`、DOM 元素 stub（同时支持 `getAttribute` + `Reflect.get`）、favicon/meta 指纹
  5. `signtool_new` 间歇性 panic（~30%）→ 重置 heap + 重新实例化重试（`run_sign.js` 内置 30 次）
  6. 非确定性来自 `crypto.getRandomValues`；覆写为固定 0x42 后输出确定 → `verify_fixed.js` 用于算法一致性验证

## 复现

```bash
# 依赖: node.js (WASM 必需) + Python 标准库 (0 第三方)
python main.py            # 结构/确定性/边界 11 项验证
python main.py --live     # 追加真实请求验证 (需网络)
```

| 验证项 | 结果 |
|--------|------|
| 固定 nonce 期望值 ×3（2026-08-19 Node 捕获，前缀 `NQu2qdIWBMsi_` 与原项目浏览器输出逐位一致） | ✅ |
| 固定 nonce 确定性 ×1（两次字节一致）/ 随机 nonce 非确定性 ×1 | ✅ |
| PATH 覆盖边界（带 query → 124 字符）×1 / extract_path ×1 / sign_headers 组装 ×1 | ✅ |
| UA 补丁与 run_sign.js 一致 ×1 / wasm 模块完整性 ×1 / 签名 charset ×1 | ✅ |

## 验证与实测

- 样例对比：11/11 通过；签名长度随 PATH 变化（92/96/100/124 四档）均与预期一致
- 真实请求验证：原项目 2026-06-21 端到端 6/6 接口 200（artworks recent/hot、predict tags、vacation config 等）；`python main.py --live` 可现场复测

## 备注

- 失效风险：UA 硬编码于 `run_sign.js` 第 86 行，浏览器版本升级需同步；WASM 文件名带 hash；固定 0x42 低熵签名会被服务端拒绝（仅用于算法验证）
- 坑：签名只签 PATH（query 会 403）；UA 必须与签名内嵌值一致；Node 主进程缺 `Window` 构造函数会 panic；无效签名长度正常（重试而非判长）
