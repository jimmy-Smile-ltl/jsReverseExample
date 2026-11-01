# 去哪儿 机票 Bella 签名 — HmacSHA1 + 自定义 65 字母表 base64

> 复现对象：`spider research/OTA 在线旅游/qunar/bella.py` · 技术分类：`encrypt` · 状态：✅ 可复现

## 站点与目标

- 站点：https://m.flight.qunar.com（去哪儿 H5 机票搜索；主页无风控，搜索必带签名）
- 加密参数：`Bella`（五段式长串，v1 约 910B / v2 约 1090B）
- 目标接口：`POST https://m.flight.qunar.com/api/touchInnerList`（国内机票列表）

## 技术要点

- 算法/保护类型：HmacSHA1 + 自定义 65 字符表 base64（含 `v = 63 - v` 逐位取反），**无第三方库**
- 混淆情况：webpack inline bundle，Bella 挂在 `window` 上可直接调用（无需逆混淆）
- 一句话概括：`june_v ## sign ## cipher ## random21 ## keyArray`；v2 的 `sign = HmacSHA1(JSON(params)+random21+JSON(keys))`，再把 `sign/randomNum/t` 塞进 envMap 加密成 `cipher`

## 逆向摘要

- 入口定位：页面 `window.Bella` 直接可用 → 固定 params/env/随机源后逐字节对拍，比挖 bundle 快一个量级
- 还原过程：
  1. `june_v` = 页面加载时间戳（10 位），`random21` = 从 64 字符表（`-_` + base36 逆序 36..0 + 大写逆序 35..10）取 21 位
  2. `cipher` = `encodeURIComponent(JSON(envMap))` → 空格补足 3 倍数 → 每字节 8bit 拼接 → 每 6bit 一值 → **取反** → 65 字母表；envMap 固定 8 键（referer/piccolo/shirley/title/keywords/description/host/scriptSrc）
  3. v1 与 v2 差异：v1 把 cipher 也纳入 HMAC 且明文不含 sign；**线上走 v2**——sign 用不含 cipher 的原文算，算完再回填明文，且明文多出 `t`（毫秒时间戳）
  4. 取反只对 qunar/tujia 域名生效（同一套 SDK，域名分支），其它域 `invert=False`
- `decode_payload()` 可反向解出 envMap，样例第 3 组即用真值 Bella 反解自证

## 复现

```bash
# 依赖: 仅标准库 (hashlib / hmac / json / random)
python main.py
```

- 样例输入 → 期望输出（`SAMPLE_CASES`，2026-10-31 页面 `window.Bella` 真值，随机源与时间已钉死）：

| 输入 | 期望输出 |
|------|---------|
| v1：北京→上海 2026-11-05，random21=`LS4CSXlrN3EPLUXcGCbPu` | 910B Bella，sign 前 8 位 `b903aee4` |
| v2：同参数，random21=`Ur_huvV7EHo2WSQsx_NTV`，t=1793451187933 | 1090B Bella，sign 前 8 位 `a95fc55c` |
| v2 真值反解 | cipher 解出 sign/randomNum/t 与前三段一致 |

## 验证与实测

- 样例对比：3/3 全部通过，两组真值 **逐字节相等**（不是前缀匹配）
- 真实请求验证：2026-10-31 签名与页面一致；但 `touchInnerList` 对本机出口 IP 数据层软屏蔽（恒 `code:1999` 空结果，**真实 Chrome 同参数同样为空**），签名正确性以字节对拍为准

## 备注

- 失效风险：`june_v` 是页面级时间戳，需随会话刷新；65 字母表与服务端密钥 `h8fsaK3wqe+ioMvs` 若轮换需重提
- 坑：**取反开关按域名走**，qunar/tujia 取反、其它域不取反，抄错会得到长度对但内容错的串；v1/v2 不是版本号选择，抓包看到 5 段里明文有 `t` 就是 v2
