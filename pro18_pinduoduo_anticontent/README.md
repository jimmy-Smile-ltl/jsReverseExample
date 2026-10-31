# 拼多多 anti_content — 自定义序列化 + zlib + budget 扰码 base64

> 复现对象：`经典 不开源/拼多多-anti_content逆向-2026-08-30` · 技术分类：`encrypt` `env` · 状态：✅ 可复现（离线 20/20；Node 互证 23/23；线上 HTTP 200，2026-10-31）

## 站点与目标

- 站点：`https://www.pinduoduo.com/home/girlclothes/`（Next.js SSR）
- 加密参数：Query `anti_content`（`0aq` + 372~378 字符）
- 目标接口：`GET https://apiv2.pinduoduo.com/api/gindex/tf/query_tf_goods_info?tf_id=...&page=...&size=...&anti_content=...`
- 调用链：页面 `getGoods()` → `TPp2.a()` → `fbeZ.messagePackSync()`（85KB 混淆引擎）；`server_time` 取自 `/api/server/_stm`（失败回退 `Date.now()/1000`）

## 技术要点

- 真实流水线：22 个 collector → 自定义二进制序列化 ~340B → zlib level 6（头 `78 9C`）→ 追加 4B build CRC → budget 扰码 base64 → `0aq` 前缀
- **推翻早期“RC4”误判**：直接按标准 base64 解码得到 `D1 AA` 开头，只是未反扰码的假象；扰码是单值 `v` 平移 6bit 索引的可逆双射，无密钥、非加密
- 序列化原语：`va` LEB128 / `nc` 大端最小字节 / `ek`（`tag<<3|len`，尾随字段例外）
- 混淆情况：obfuscator.io RC4 字符串表 + 嵌套 webpack 17 模块；纯算法只需 3 个 build 常量（`ET` / `TAG7_CRC` / `WT_FLAGS`）

## 逆向摘要

- 入口定位：XHR 断点命中 `query_tf_goods_info` → 回溯 `TPp2.a()` → `fbeZ`；AST 提取嵌套 webpack 模块，字符串表按“锚点串”（split/toString/join）验证后还原
- 还原过程：
  1. `decode_strings` 解字符串表 → 得到 `encode()`：标准 base64 分组 + `_budget(t,v)` 平移 + 末尾 marker `ALPHABET[v]`
  2. 双层插桩（`A/F/ET` 与独立 `PBC`）交叉验证；`ET = crc32(Wt源码+ue源码)`，任何源码 hook 都会污染该值
  3. 21 字段逐段对齐：`device_id = str(p1+p2) + "-" + serverTime`（数值相加，非拼接），nano 校验位**右补 0**
  4. 解码回验：反扰码 → `78 9C` → zlib 解压 → `[03 01 00 00] + 2B BE 长度 + 字段`
- JS→Python 差异：`Math.random` 调用顺序（device_id 2 次 → nano 21 次 → `v`）必须守恒；`crc32`、`ljust(3,"0")`、`zlib.compress(level=6)` 与 pako 默认一致

## 复现

```bash
# 仅标准库；--node/--live 可选
py main.py           # 20 项：原语 + 编码器 + 3 组确定性向量 + 结构/回环
py main.py --node    # +3 项：generator/ 原版引擎，输出用同一解码器互证
py main.py --live    # +1 项：纯算法生成 → 真实 API 请求
```

| 输入（seed, server_time, init_ms, now_ms, counter） | 期望输出 |
|------|---------|
| `20260829, 1788020797, 1788020797000, 1788020797113, 1` | `0aqAfxUeMwVEQ_Jy...`（376） |
| `20260830, 1788050000, 1788050000000, 1788050000237, 5` | `0aqWtxUkM_VeTpYy...`（374） |
| `20260901, 1788100000, 1788100000000, 1788100000891, 42` | `0aqWtxUkM_Ve2qay...`（372） |

## 验证与实测

- 离线：`py main.py` 20/20 通过；3 组向量与经典纯算法（同 seed/时间）逐字节一致；每组解码回环 `反扰码 → zlib(6) → 字段断言` 全通过
- Node 互证：`--node` 23/23，原版引擎输出用本仓库解码器反解出 `78 9C + ET + 合法 payload`，证明“无 RC4”结论
- 线上：2026-10-31 纯算法直连 `HTTP 200, success=True`，返回 3 条商品；经典项目 2026-08-29 5/5、08-30 3/3
- 早期补环境路线留存于 `generator/`（原版 bundle + env/mocks），作为版本轮换时的兜底与对照

## 备注

- 失效风险：换 build 时重捕获 `ET`、`TAG7_CRC`、`WT_FLAGS`；字段结构变化需用 `parse_a.js` 重拆
- 坑：插桩改源码会改变 `crc32(fn.toString())`；`et` 真值 `0x2307ED43` 由独立 PBC hook 互证
- 样例为确定性合成向量（固定 seed/时间），不含真实设备/用户数据；生产直接调用 `generate_anti_content()`
