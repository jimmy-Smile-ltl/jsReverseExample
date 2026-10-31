# BOSS直聘 __zp_stoken__ — JSVMP 双层虚拟机

> 复现对象：`经典 不开源/BOSS直聘-JSVMP逆向-2026-08-29` · 技术分类：`vm` `env` `encrypt` · 状态：✅ 可复现（离线 3/3；线上 5/5，2026-08-29）

## 站点与目标

- 站点：`https://m.zhipin.com/`（2026-08 版本 `393d5208`，前缀 `523e`）
- 加密参数：Cookie `__zp_stoken__`（453~473 字符，`523eg` + base64）
- 目标接口：受保护页面先 302 到挑战 URL（`seed` 44 字符 base64 + `name` JS 文件名 + `ts` 毫秒），生成 token 后带 Cookie 与 `_security_check=1_<now>` 重放返回 200

## 技术要点

- 保护类型：JSVMP 双层解释器（451 个 VM 程序），token = `"523e" + "g" + base64(UTF8变体(P))`
- 环境依赖：186 项环境指纹常量 + 1001 项 window 属性 / 1213 键 CSS / canvas 指纹等采集
- 服务端校验：seed 绑定 + ts 时间窗 + 结构一致性 + 环境新鲜度；`key` 等随机分量必须真随机

## 逆向摘要

- 入口定位：302 跳转 URL 的 `name` 参数即当轮 VM 文件名；`seed`/`ts` 直接进入 VM 构建链
- 还原过程：
  1. 真实 Chrome 与 Node 沙箱逐指令轨迹 diff，定位 `t/Y2/Y/key/head` 构建链与 186 项环境模板
  2. `ts_sec = ts//1000`；`t = [4]+ord("523e,")+ord(seed)+[240, ts_sec 4B, floor(LCG()*100)]`
  3. `Y2[k] = t[k] + (k 偶数 ? k : 2k)`；`Y = [56] + Y2 + ENV`；`X[i] = (Y[i]+3) ^ ord(str(key)[i%5])`
  4. `P = ((((head+X)+12)^3)+5)^1`，按 **2 字节 overlong UTF-8 变体**编码后 base64
- JS→Python 差异：LCG 输出含 `& 0x7FFFFFFF` 掩码；`env[113:117]` 与 `env[151:154]` 时间副本必须同步

## 复现

```bash
# 仅标准库，无需网络
py main.py                    # 3 组固定随机源向量：生成 → 逐字节比对 → 逆解结构断言
py main.py --gen SEED TS      # 用当前时间生成一条 token（env 时间自动刷新）
node reference/live_check.js  # 可选：抓 302 → 生成 → 重放（2026-08-29 实测 5/5）
```

| 输入（seed 相同，固定 lcg_seed/rand_seed/env_ts） | 期望输出 |
|------|---------|
| `ts=1781494113632, lcg=123456789, rand=42` | 453 字符，`523egw5Icw4IeTxw...` |
| `ts=1781494173632, lcg=987654321, rand=7` | 453 字符，`523egw5XDpcO8H0k...` |
| `ts=1781494233632, lcg=555555555, rand=2026` | 457 字符，`523egw5XCusKTHEk...` |

## 验证与实测

- 离线：`py main.py` 3/3 通过；`decode_token` 独立逆解出 seed/ts/key/env_ts 并与输入一致
- 线上：2026-08-29 五轮「302 挑战 → 纯算法 token → 重放」全部 200（`reference/live_check.js` 同轮执行）

## 备注

- 失效风险：VM 版本随 302 的 `name` 轮换；升级需重跑生产轨迹并更新前缀/构建链常量
- 坑：确定性 token 会被服务端拒绝（随机分量必须真随机）；seed/ts 仅当轮有效（约 10 分钟），生成与回放必须同轮
- 样例 seed/ts/env_ts 均已过期，仅用于离线算法比对，不能用于真实请求
