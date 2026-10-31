# 京东主站 h5st v5.3 — 段结构与 seg7 编解码（部分复现）

> 复现对象：`经典 不开源/京东主站-h5st签名-2026-08-30` · 技术分类：`vm` `encrypt` `env` · 状态：🔒 仅样例（结构 + seg7 可复现；哈希链未还原）

## 站点与目标

- 站点：`https://www.jd.com/`（2026-08 版 `h5_file_v5.3.4`，appId `b5216`）
- 加密参数：Query `h5st`（10 段 `;` 分隔，共 1103 字符）
- 目标接口：主站商品/搜索 API；请求层另有 TLS 指纹 WAF（601/403 需 curl_cffi）

## 技术要点

- 保护类型：35 解释器 VM（SDK `sign.js`）+ 自定义 base64 双重块乱序 + env 语义校验
- 段结构：`date;fp;appId;token;seg5;5.3;ts13;seg7;seg9;seg10`
- 服务端校验（逐段替换实验）：date 时效 ✅、fp↔token 绑定 ✅、seg7 env 字段语义 ✅、seg8 hash ✅；seg4 / ts13 / seg9 不校验

## 逆向摘要

- 入口定位：主站 `sign.js` 的 `h5st` 生成函数；XHR 断点回溯到 `signer._algos`
- 还原过程：
  1. 逐段替换实验先确定「服务端校验什么」，把 10 段缩到 seg7/seg8 两个真目标
  2. 分段 diff 定位缺口：Node 输出 1059 vs 浏览器 1103 → 44 字符全在 seg7（webglFp 为空）
  3. `seg7 = rev4(customB64(rev3(PKCS7(JSON indent=2))))`；`seg10 = 同链("appid,body,functionId"+b"\x03"×3)`
  4. 卡点：主站 `signer._algos.SHA256` 是**变体**（`"abc"` 摘要与标准 SHA256 不同），seg4/5/8/9 无法用 hashlib 复现
- JS→Python 差异：JSON 必须 2 空格缩进并 PKCS7 补到 3 的倍数；块序反转以 3 字节块为单位，字符逆序以 4 字符组为单位

## 复现

```bash
# 仅标准库
py main.py                 # 3/3：seg10 常量、seg7 解码/重编码、10 段结构
py main.py --decode "<h5st>"   # 解出 seg7 的 env JSON
```

| 输入 | 期望输出 |
|------|---------|
| `seg10 = of7rHGHQ8GlOIyVOF6ZNHuFT-bVR7qUT` | 解码为 `appid,body,functionId\x03\x03\x03`，可重编码回原串 |
| 脱敏 `seg7`（788 字符） | 解出 13 键 env：`v=h5_file_v5.3.4`、`fp=sanitizedfp00001`、`t=1788024996279` |
| 脱敏 `h5st`（1103 字符） | 10 段，长度 `[17,16,5,92,64,3,13,788,64,32]` |

## 验证与实测

- 离线：`py main.py` 3/3 通过；真实捕获（2026-08-30）的 seg7 解码后再编码与原文逐字节一致
- 线上：补环境 + curl_cffi 实测 `code=0`（2026-08-30，原项目记录）；纯 Python 未打通哈希链，故本仓库不提供完整签名
- 参考路线：`reference/sign_v53_pure.js`（cactus 刷 token + SDK 生成；依赖的 `sign.js` / `local_cache.json` 未随仓库分发）

## 备注

- 失效风险：SDK 版本随主站下发轮换；seg7 env 会随浏览器环境变化（`ls/wk/bu*`）
- 坑：seg7 不是简单的「追加 0x01」（早期 JS 工具链注释有误），实测是 PKCS7 补齐；只换 IV 类实验对 hash 链无效
- 样例 fp/canvas/webglFp 已替换为占位值，token 为占位串；仅用于离线结构验证，不能用于真实请求
