# 财联社电报 sign — SHA1→MD5 双重哈希签名

> 复现对象：`spider research/其他/pro10 财联社/rpc/sign.py` · 技术分类：`encrypt` · 状态：✅ 可复现

## 站点与目标

- 站点：https://www.cls.cn（财联社电报，财经快讯平台）
- 加密参数：`sign`（每个 GET 请求必带的 32 位小写 hex 签名，错误则返回 401）
- 目标接口：`GET https://www.cls.cn/nodeapi/telegraphList`（电报列表）、`/nodeapi/telegraph`（单条电报）

## 技术要点

- 算法/保护类型：`sign = MD5(SHA1(query_string))` 双重哈希签名
- 混淆情况：webpack bundle（_app.js 545KB），sign 函数位于 module 36498，SHA1 为 Rusha 实现、MD5 为 module 81383
- 一句话概括：参数按 key 大写排序 → 递归序列化（嵌套 dict/list 展开为 `key[nested][idx]=value`）→ `&` 连接 → SHA1 → MD5 得 sign

## 逆向摘要

- 入口定位：浏览器 F12 搜索 `sign` 关键字 → 定位 webpack module 36498；请求带错 sign 实测 401 确认生效
- 还原过程：
  1. 从 545KB bundle 提取 sign 函数（依赖 Rusha SHA1 + MD5 两个模块，纯 JS 无环境依赖）
  2. JS→Python 关键差异：排序用 `k.toUpperCase()` 比较（`sorted(key=str.upper)`）；bool 小写序列化；None 跳过；空数组输出 `key[]`
  3. 抓包采集 5 组真实请求（含嵌套参数：fields/secu_codes/type+way），Python 输出与浏览器 sign 逐组比对
- 另有两套方案存档：env_patch/（补环境跑原版 bundle）与 rpc/（Node RPC），本复现取纯算路线

## 复现

```bash
# 依赖: 仅标准库 hashlib
python main.py
```

- 样例输入 → 期望输出（内置在 `main.py` 的 `SAMPLE_CASES`，5 组，2026-06 抓包）：

| 输入（params） | 期望 sign |
|------|---------|
| `{app, os, sv}` | `b02d8f7bc4c45eeb3e86904203597da2` |
| `{app, name=telegraph, os, sv}` | `6c73b056a64891cdc257dcf1914464ad` |
| `{app, lastTime, name=telegraphList, os, sv}` | `08c4bd752e9f95afbbec3283a6564cf6` |
| `{app, fields, os, secu_codes, sv}`（嵌套键） | `9e0b2a4b062fadc82407b8b50982a164` |
| `{app, os, rever, sv, type, way}` | `00231877ba09a2a8b50daa83c7422b48` |

## 验证与实测

- 样例对比：5/5 全部通过（含嵌套参数序列化路径）
- 真实请求验证：2026-06 抓包采集时 sign 校验通过（telegraph_output.json 存有 100 条成功采集结果）；此后未重测，接口可能要求额外 header（如 Referer）

## 备注

- 失效风险：sv 版本号（8.7.9）随 App 更新可能变化，sign 算法本身长期稳定；接口可能有频率限制
- 坑：key 排序必须不区分大小写（`app` 与 `APP` 同序），用 `sorted(key=str.upper)` 而不是默认比较；Rusha SHA1 输出与 `hashlib.sha1().hexdigest()` 完全一致，无需自定义实现
