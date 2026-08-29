# 今日头条 a_bogus — 补环境离线签名引擎

> 复现对象：`spider research/其他/pro3 今日头条 JS逆向/extract/` · 技术分类：`encrypt vm env` · 状态：✅ 可复现（签名离线生成，实测 3/3 通过）

## 站点与目标

- 站点：https://www.toutiao.com（头条资讯流）
- 加密参数：`a_bogus`（动态签名，168/172 位，取决于环境完整度，两者均有效）、`msToken`（120 位设备令牌）
- 目标接口：`GET https://www.toutiao.com/api/pc/list/feed`（信息流列表，缺签名返回验证错误）

## 技术要点

- 算法/保护类型：VM 字节码签名（bdms.js 解释器 + 签名字节码）+ fetch 拦截器自动附加签名 + TLS 指纹校验（需 curl_cffi `impersonate="chrome146"`）
- 混淆情况：webpack 多模块（sdk-glue 168 模块 / bdms 196 模块），签名逻辑藏在 VM 字节码中，不直接可见
- 一句话概括：补环境加载原版 SDK 四件套，Hook `URLSearchParams` 捕获 SDK 自动附加的 a_bogus/msToken

## 逆向摘要

- 入口定位：抓包发现 `/api/pc/list/feed?…&a_bogus=…&msToken=…` → 搜索关键字定位 sdk-glue → bdms VM 解释器
- 还原过程：
  1. 架构链：`acrawler.js`（爬虫检测）→ `sdk-glue.js`（胶水层）→ `bdms.js`（VM 解释器 + 签名字节码）→ `runtime_bundler.js`（拦截器框架，注册 FETCH_REQUEST 钩子）
  2. 双路线：**补环境**（toutiao_env_full.js + dom_prototypes.js 在 Node 里伪装浏览器）与 **浏览器 RPC**（rpc/test_direct.py，WebSocket 桥接真实页面）
  3. 补环境档产出 168 位 a_bogus（浏览器档 172 位，差 4 位），实测浏览器 164 位亦可用 → 长度非核心约束
  4. 核心手法：Hook `URLSearchParams` 序列化时机捕获 SDK 追加的签名参数，不解析 VM 字节码
- JS→Python 差异：签名含随机/时间因子无固定期望值；Python 侧只做「长度 ∈ {164,168,172} + base64url 混合字符集」结构校验

## 复现

```bash
# 依赖: node (v16+, 实测 v24) + Python 标准库 (subprocess 调用 node)
python main.py
```

- 样例输入 → 校验规则（签名每次不同，无法固定比对，3 组参数取自 2026-04~06 抓包）：

| 输入（参数串） | 校验规则 |
|------|---------|
| `channel_id=0&…category=pc_profile_recommend&aid=24&app_name=toutiao_web` | a_bogus 长度 ∈ {164,168,172}，msToken 120，字符集合法 |
| `offset=0&channel_id=94349549395&…pc_profile_channel…` | 同上 |
| `offset=0&channel_id=3189398996&max_behot_time=1725964720…` | 同上 |

## 验证与实测

- 样例对比：3/3 全部通过（每次运行输出 168 位 a_bogus + 120 位 msToken）
- 真实请求验证：2026-04 原项目浏览器 RPC 方案实测 Status 200、Article count 12；补环境签名需配 curl_cffi（chrome146）过 TLS 指纹后实测（见原项目 try_toutiao.py）

## 备注

- 失效风险：SDK 版本升级后 a_bogus 算法/模块名可能变化；msToken 原版从 localStorage.xmst 读取，补环境用固定种子
- 坑：`require("coreLoader")` 由 runtime_bundler_52.js 内部自洽提供，迁移时勿删该文件；a_bogus 字符集是 base64 与 URL-safe（`-`/`_`）混合，做字符集校验时要并入
- 目录内 bdms_browser.js / sdk-glue.js / runtime_bundler_52.js 为头条原版 SDK（webpack 打包），仅作学习研究归档
