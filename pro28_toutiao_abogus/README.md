# 今日头条 a_bogus — bdms VM 还原为纯算法（148 字符）

> 复现对象：`经典 不开源/今日头条-a_bogus签名-2026-09-02` · 技术分类：`vm` `encrypt` · 状态：✅ 可复现（离线 7/7；Node 备份 10/10；线上 HTTP 200，2026-10-31）

## 站点与目标

- 站点：`https://www.toutiao.com/`（PC 推荐流）
- 加密参数：Query `a_bogus`（2026-09 版 148 字符；旧版 164/168/172 字符服务端仍兼容）
- 目标接口：`GET https://www.toutiao.com/api/pc/list/feed?channel_id=...&max_behot_time=...&a_bogus=...`
- 调用链：`acrawler.js` → `sdk-glue.js` → `bdms` VM（26 blob / 25 派发站点）→ `runtime_bundler` fetch 拦截器 → 自动追加签名

## 技术要点

- 保护类型：bdms 字节码 VM（签名 blob#24，3184B）+ fetch 拦截；每个派发站点 opcode 表不同
- 纯算法结构：`inner = UA XOR RC4([0,9,14])` → 三重 `be_sum` 哈希 → 44 值流 + 反汇编顺序 XOR 校验 → 55B 尾部 → `(99B) XOR RC4('y')` → `head12 + body` 自定义 base64
- `be_sum`：SHA-256 骨架的深度定制（轮常数两段且每轮 `rotL(K,f)`、`c=rotL(b,9)`、状态 XOR 合并、68 项调度 + `w'[a]=w[a]^w[a+4]`）
- 服务端校验：签名字节 + ink 新鲜度（~30s）+ 时间戳；**msToken / cookie / referer / TLS 均不校验**

## 逆向摘要

- 入口定位：抓包 `/api/pc/list/feed` → 定位 sdk-glue → bdms；patch 暴露签名闭包 `__signer/__be/__re` 后直接喂输入
- 还原过程：
  1. 源码级提取：从主 blob 生成代码中取出 `be` 类（3026 字符）+ 4 个辅助函数，15/15 向量验证
  2. 运行时探针：wrap 闭包记 I/O、hook `fromCharCode/charCodeAt` 追字节流、mulberry32 + 固定时间做字节级 diff
  3. “内层递归”实为 `UA XOR RC4([0,9,14])`（调用计数证明 `re` 只调 2 次，无深层递归）
  4. 44 值校验链逐条对照反汇编转写；head12 随机头不校验，写死即可
- JS→Python 差异：`be_sum` 的填充与 8 字节大端位长、`(x<<n)` ToInt32 截断；`score` 固定 9；`ink = now_ms`

## 复现

```bash
# 纯算法仅标准库；--node 需 node（旧版 168 字符 + msToken 备份路线）
py main.py           # 7 项：be_sum/RC4 组件 + 3 组确定性向量 + 时间敏感
py main.py --node    # +3 项：旧版补环境引擎（168 字符 + msToken 120）
py main.py --live    # +1 项：纯算法签名 → 30 秒内请求真实 feed
```

| 输入（query 摘要, now_ms） | 期望输出（148 字符） |
|------|---------|
| `pc_profile_recommend, offset=0, max=1788312759` @ `1788312759000` | `Q78ZMR8DDkgs...` |
| `pc_profile_recommend, offset=20, max=1788320000` @ `1788320000123` | `Q78ZMR8DDkgs...` |
| `pc_profile_channel, channel=94349549395` @ `1788333333456` | `Q78ZMR8DDkgs...` |

## 验证与实测

- 离线：`py main.py` 7/7；`be_sum('cus')`、双重 sum、RC4 标准向量、3 组向量与经典纯算法逐字节一致
- 备份：`--node` 10/10，旧版 SDK 产出 168 字符 a_bogus + 120 字符 msToken（长度/字符集校验）
- 线上：2026-10-31 纯算法 + 裸 urllib 实测 `HTTP 200, success=True`（513KB feed）；经典项目 2026-09-02 翻页 5/5
- 时效：ink 必须新鲜（~30s 窗口），签完立即发请求；过期只换时间重签

## 备注

- 失效风险：SDK 换版需重跑 `sign_dump.js`/`diff_det.js` 重新定位常量；结构（sum/RC4/base64/流布局）大概率不变
- 坑：`vendorSubs.ink` 不能硬编码测试值（曾导致数天误判）；`be_sum` 填充循环照抄原源码；字符集含 `-`/`_`
- 第三方文件：`bdms_browser.js` / `sdk-glue.js` / `runtime_bundler_52.js` 版权归字节跳动，仅作学习研究归档，不用于分发或商用
- 样例为固定时间戳的离线向量，服务端已过期，仅用于算法比对
