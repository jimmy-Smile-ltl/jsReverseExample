# 雪球网 — md5__1038 WAF 签名参数加密

> 复现对象：`经典 不开源/雪球网-md5__1038-WAF签名-2026-08-16`（原 `spider research/财经/pro1 雪球网/`）· 技术分类：`encrypt` `waf` · 状态：✅ 可复现（离线 10/10；含 Node 对拍 13/13，2026-10-31）

## 站点与目标

- 站点：`https://xueqiu.com/`（2026-08 实测；签名算法 2026-08-16 版）
- 加密参数：URL 查询参数 `md5__1038`，格式 `<salt>-<LZW 编码>`，salt = `222029ad07`
- 目标接口：全部 API（如 `/statuses/fundx/public/list.json`），缺签名被 WAF 302 到认证页

## 技术要点

- 算法：SHA1[10:26] → 随机 0x2X 异或 → 环境 bit 打包 → 自定义 LZW + 6-bit 字符表
- 保护类型：WAF 签名；SDK 已迭代 3 代（salt/字符表均变），当前字符表 65 字符

## 技术路线对比

| 路线 | 位置 | 状态 | 说明 |
|------|------|------|------|
| 01-补环境 | 经典归档 | 归档 | vm 沙箱还原，受 Web Crypto 限制 |
| 02-精简补环境 | 经典归档 | 归档 | 裁剪环境，仍依赖 Node |
| 03-纯算 | 经典归档 | 半成品 | 仅 token 编解码，未完成 encode |
| 04-RPC | 经典归档 | 100%（归档记录） | Playwright + WebSocket，最稳但重 |
| 纯算 | **本仓库 main.py** | ✅ 13/13 | 全算法 + 手写 LZW 解码器 |
| Node 直算 | **本仓库 md1038_generator.js** | ✅ | 原 webpack 函数逐行移植；`reference/` 固定随机源对拍 |

## 逆向摘要

- 入口：页面 renderData 取 `_waf_bd8ce2ce37`（wafToken）→ XHR 断点定位 `a4()` → webpack 还原 `md5_1038`
- `mp = encodeURIComponent(wafToken + method + salt + api)`；`mu = mp + encodeURIComponent(fingerprint)`
- `m2 = SHA1[10:26]`；`m4` 每 2 hex 与随机 `0x20-0x2F` 异或；`F()` 环境 bit（Fisher-Yates）
- `mc = mc1|mc2|mc3|mc4|wafToken|serverTs|mc7`；LZW 9bit 起、每 512 码 +1bit、KwKwK
- JS→Python：`quote(safe="")` 与 `encodeURIComponent` 并不等价（前者会编码 `!'()*`，而 UA 指纹含括号），必须 `safe="!'()*-._~"`

## 复现

```bash
# 仅标准库；--node 需本机 node
py main.py           # 13 项：m2 + LZW + 3 组确定性向量 + 随机性
py main.py --node    # +3 项：同随机序列/时间，JS 与 Python 逐字节一致
```

| 输入（wafToken / api / now_ms） | 期望输出 |
|------|---------|
| `0M6LZ...E0=` / `list.json` / `1788025000123` | `222029ad07-t20A/...dT2b`（194） |
| `0M6LZ...E0=` / `list.json?source=fund_public&page=1` / `1788036000456` | `222029ad07-IvcA...a_P8`（200） |
| `EXPIRED_TEST_TOKEN...=` / `list.json` / `1788047000789` | `222029ad07-2gfI...AB5`（158） |

## 验证与实测

- 离线：`py main.py` 10/10；3 组向量由固定随机序列（48 次调用）+ 固定时间生成，逐字节一致
- 交叉：`py main.py --node` 13/13，同一序列下 JS 生成结果与 Python 完全相同（含 mc1/mc2/mc3/mc4/mc7）
- 线上：经典归档 2026-08-16 补环境方案签名被服务端接受（页面 200 + API 200）；RPC 方案 100%
- 样例：`wafToken`/`serverTs` 为 2026-08 已过期抓包值，仅用于算法比对，不可直接回放

## 备注

- 失效风险：salt/字符表随 SDK 换代（8 月已变一次）；wafToken 有会话时效
- 坑：LZW 字符表实际 65 字符（含 `=`），非表字符映射为 `65+charcode`；随机调用顺序（m4 16 次 → F 31 次 → mc7 1 次）必须守恒
- 参考：`reference/node_deterministic.js` 用固定 `Math.random`/`Date` 复现 JS 侧字节流，可重生成样例
