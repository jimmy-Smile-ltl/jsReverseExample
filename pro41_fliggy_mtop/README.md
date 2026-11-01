# 飞猪 MTOP 签名 — md5(token & t & appKey & data)

> 复现对象：`spider research/OTA 在线旅游/fliggy/fliggy_mtop.py` · 技术分类：`encrypt` · 状态：✅ 可复现

## 站点与目标

- 站点：https://www.fliggy.com（H5 SPA 跑在 `market.m.taobao.com/app/trip/*`）
- 加密参数：`sign`（32 位小写 hex），配套 `t`、`appKey`、`ttid`、`data`
- 目标接口：`POST https://h5api.m.taobao.com/h5/mtop.trip.search.srp.pattern.render/1.0`（搜索）、`mtop.fliggy.ssif.pattern.home`（首页 feed）

## 技术要点

- 算法/保护类型：阿里 MTOP 标准签名 `sign = md5(token & t & appKey & data)`，无混淆、无自定义加密
- 混淆情况：无（MTOP 是协议层签名，前端只做参数拼装）
- 一句话概括：token 取自 `_m_h5_tk` Cookie 首段，t 是毫秒时间戳，data 是请求体字符串——**data 必须与 URL 里传的逐字节一致**

## 逆向摘要

- 入口定位：抓请求直接可读——query 里就有 `sign/t/appKey/data` 四件套，`_m_h5_tk` Cookie 一眼可见
- 还原过程：
  1. 首次不带 token/sign 调用 → 返回 `FAIL_SYS_TOKEN_EMPTY::令牌为空`，同时 `Set-Cookie: _m_h5_tk=<token>_<expire_ms>`
  2. `token = value.split("_")[0]`，`sign = md5(f"{token}&{t}&{APP_KEY}&{data}")`，同参数重发即 `SUCCESS::调用成功`
  3. **网关选择有讲究**：trip 系列接口走 `h5api.m.taobao.com`（调用方是 taobao 域的 SPA），`h5api.m.fliggy.com` 返回 `FAIL_SYS_ILLEGAL_ACCESS`
  4. **payload 必须 args 包裹**：`{"bizType","name","version","platform","args","isLocationPermission","h5Version"}`，`args` 是二次编码的 JSON 字符串
  5. 内外层序列化不一致：外层 compact，内层 `args` 用带空格的默认分隔符——空格的差异会直接改变 md5

## 复现

```bash
# 依赖: 仅标准库 (hashlib / json)
python main.py
```

| 输入（2026-11-01 同会话真机抓包） | 期望 sign |
|------|---------|
| 搜索「云南」page=3 size=5，t=1793514768474 | `4d49ea199132bf434074c3f08474ddcf` |
| 首页 feed page=3，t=1793514769427 | `8f07c471788d029b3866e19de3051470` |
| 搜索「大理」page=1 size=5，t=1793514769717 | `d4aea465c2214a191d55cd350e1dcd07` |

- 另有 token 提取 / 无 token 不带 sign / URL 形态三项自检，共 4/4 通过

## 验证与实测

- 样例对比：3/3 sign 逐字节相等（data 串由 `search_data()`/`feed_data()` 现算，等于抓包原件）
- 真实请求验证：2026-11-01 单会话 3/3 `SUCCESS::调用成功`；搜索翻页 p1~p4 各 14~18 条，按 `itemId` 去重；`pageSize=100` 实返 ~77 条
- 频控：token 约 1 小时轮换，过期后重新握手即可；无账号态也可用

## 备注

- 失效风险：`appKey`/`ttid` 随 H5 包版本变化；`h5Version`（2.23.11 / 2.1.8）写死在 payload 里，服务端目前不校验
- 坑一：**data 字符串是签名的一部分**，用 dict 传参会因序列化差异（空格/中文转义）算出错误 sign；本实现保留内层默认分隔符，与真机一致
- 坑二：平铺参数（把 `keyword` 直接放最外层）会返回 `SUCCESS` 但 `data` 只有 2 字节——不是签名错，是结构错，容易误判
