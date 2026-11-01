# 途家 Revelio 风控报文 — 字符串表轮转还原 AES-GCM 密钥

> 复现对象：`spider research/OTA 在线旅游/tujia/revelio_gen.py` · 技术分类：`encrypt` `obfuscate` · 状态：✅ 可复现

## 站点与目标

- 站点：https://m.tujia.com（途家民宿 H5）
- 加密参数：`/revelio/report` 的请求体 `data.{iv,salt,txt}`（AES-GCM），返回 token 组装 `_tujia_rvl_` Cookie
- 目标接口：`POST https://m.tujia.com/revelio/report`（风控指纹上报，换 token）

## 技术要点

- 算法/保护类型：WebCrypto **AES-GCM**（12B nonce，16B 随机 salt 不参与加密），密钥藏在字符串表里
- 混淆情况：webpack 分包 `chunk-2d0c5538`（5.7K 行）；29 项字符串表 + 26 次 `push(shift())` 轮转
- 一句话概括：`A(n)=R()[n-211]` → 拼出 218 字符 `P[KEY]` → `slice(32,64)` 得 32 字节密钥 → AES-GCM 加密指纹 JSON

## 逆向摘要

- 入口定位：抓包见 `POST /revelio/report`，响应即 token；沿 `chunk-2d0c5538` 找到 `class Revelio.report()`
- 还原过程：
  1. `R()` 返回 29 项数组，外层 IIFE 反复 `e.push(e.shift())`，直到校验式等于 `207590` —— 实测轮转 **26 次**
  2. 校验式是 11 个 `parseInt(A(k))` 的加权和，必须按 JS 语义实现 `parseInt`（取前导数字，无数字为 `NaN`），否则永远不命中
  3. `P[KEY] = "sFOhW/…" + A(215) + "Pe5uZ7ZZZM" + A(218) + …`（19 段），拼出 218 字符，取 `[32:64]`
  4. 加密分支 `type:0`（有 `crypto.subtle`）：`iv` 12B 随机、`salt` 16B 纯随机不参与运算，明文是 `JSON.stringify(指纹对象)`
- 明文结构：`ts/str/end`（时间基准）+ `sft`（UA）/`hrd`（canvas 哈希）/`usr`/`ufp`（tuid 设备号）/`wgl`（GPU）/`env`（含上报时 cookie 串）
- 服务端只校验 **AES-GCM 可解密 + 结构**，不与 `_fas_uuid` 绑定、不比对 `env.ck` ⇒ 可本地合成指纹

## 复现

```bash
# 依赖: pip install cryptography     （AES-GCM）
python main.py
```

| 样例（`SAMPLE_CASES`） | 期望 |
|------|---------|
| 字符串表轮转还原 | 26 次轮转、218 字符、`KEY=JeYNb41mPe5uZ7ZZZMUnu34Xz4BOG1Md` |
| 固定 iv/salt 加密 | 732 字符密文（钉死输入才可复现，AES-GCM 本身随机） |
| 解密回环 | 解出与 `FIXED_PLAIN` 完全相等 |
| 模板时间平移 + 设备号替换 | `ts=5000 → str=4010 end=4020 sft.str=4005`，原模板不被改动 |

## 验证与实测

- 样例对比：4/4 全部通过（密钥可由 SDK 原表独立还原，不依赖任何网络）
- 真实数据验证：2026-10-31 抓到的 **52,521B 真实报文**用 `decrypt()` 完整解出指纹对象（含 canvas/webgl 哈希），再用 `build_payload()` 重加密上报换到 token，业务接口 `searchhouse` 返回 32,631 条房源总数
- 未入库：真实指纹模板 39.8KB（含 cookie 串与画布哈希），按 README 结构自建最小模板即可

## 备注

- 失效风险：字符串表/轮转次数随 SDK 发版变化，`rotate_table()` 的校验式需同步；密钥轮换则 `[32:64]` 切片位置不变但内容变
- 坑一：`parseInt` 必须是 JS 语义——`"355923BQpTim" → 355923`、`"abc" → NaN`，用 Python `int()` 会直接抛错
- 坑二：`salt` 是纯随机填充**不参与加密**，别把它当 AAD；`type:1` 分支（无 WebCrypto）是 CryptoJS AES-CBC + HMAC-SHA256，真实 Chrome 走不到
