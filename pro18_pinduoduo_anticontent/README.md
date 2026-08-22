# 拼多多 — anti_content 参数: 自定义二进制序列化 + zlib + RC4 + base64url

> 复现对象：`spider research/电商/pro5 拼多多/` · 技术分类：`encrypt` + `env` · 状态：✅ 可复现（RC4 密钥派生未逆向，有效串经 Node 补环境引擎生成；19/19 通过，2026-08-20 验证）

## 站点与目标

- 站点：`https://www.pinduoduo.com/home/girlclothes/`（拼多多好货频道，Next.js SSR）
- 加密参数：`anti_content`（URL query），接口 `GET https://apiv2.pinduoduo.com/api/gindex/tf/query_tf_goods_info?tf_id=...&page=...&size=...&anti_content=...`
- 调用链：组件 getGoods() → `TPp2.a()` → `fbeZ.messagePackSync()`（85KB 混淆引擎，webpack 模块在 subject.js）；server_time 取自 `/api/server/_stm`

## 技术要点

- 四层管道：自定义二进制序列化 312B → zlib deflate level 9（~270B，头 78 DA）→ RC4 流加密（~279B，**密文头恒为 D1 AA**）→ base64 URL-safe（+→-、/→_、去=，372~378 chars）
- 混淆情况：fbeZ 85KB 引擎（pako + MessagePack + RC4 字符串表，方法名动态获取）未逐行逆向
- 一句话概括：**RC4 密钥由 device_id+timestamp 在引擎内派生（未还原）**——纯 Python 只能复现 1/2/4 层，有效 anti_content 必须补环境跑原版引擎

## 逆向摘要

- 入口定位：XHR 断点 → `query_tf_goods_info` 带 `anti_content` → 调用栈 `TPp2.a()` → `fbeZ.messagePackSync()`（`x.b()` 先初始化 fbeZ，server_time 可 mock 为 `Date.now()/1000`）
- 还原过程：
  1. 二进制格式重构：固定头 `03 01 00 00 01`、`"28+"` 类型标记、URL、16 位随机 device_id、10 位时间戳、固定签名串 `XpmJX0CqlpdJX5PbnT__2~8b1uSw2S162cZb3Sp9`（出现两次）——对照抓包逐段还原，长度精确 312B
  2. 分层验证：zlib(9) 输出头 78 DA；插桩拿到三元组（zlib 明文头 XOR 密钥流 = RC4 密文头），证明 RC4 层真实存在且密钥流动态变化
  3. 补环境方案（generator/）：env.js 模拟 navigator/screen/document/window（delete MessageChannel 让 React scheduler 走 setTimeout），mocks.js 注入 s6vS/vDqi/8oxB + vendored regenerator-runtime，**跳过 commons.js**（React DOM 会崩），加载 webpack.js→main.js→subject.js，patch webpack runtime 暴露 `__webpack_require__`
- JS→Python 差异：base64 变体 `replace('+','-').replace('/','_').rstrip('=')`；`zlib.compress(data, 9)` 等价 pako 默认（zlib 格式带头）；device_id/时间戳随机 → 纯 Python 产物无法与抓包逐字节比对（只能验证结构）

## 复现

```bash
# 依赖: Python 标准库 (0 第三方) + Node.js（--node/--live 时）
python main.py         # 15 项: 结构/zlib/base64url/密钥流/抓包前缀
python main.py --node  # +3 项: 补环境生成 ×2 → 0aq 魔数/长度/非确定性
python main.py --live  # +1 项: 真实请求 → HTTP 200 + success:true
```

| 验证项 | 结果 |
|--------|------|
| generator/ 8 文件 + loader 本地化 patch ×2 + webpack patch 目标 | ✅ |
| 二进制 payload 结构 ×4（312B 常量段/device_id/时间戳/variant/签名×2） | ✅ |
| zlib 层 ×2（78 DA 头 + 长度区间 / roundtrip） | ✅ |
| base64url 层 ×2（长度公式 / 无 +/= 字符集） | ✅ |
| 密钥流三元组 XOR ×1（2026-06-07 插桩样例） | ✅ |
| 抓包前缀 ×3（0aq… → 解码头 D1 AA，2026-06-07 实存片段） | ✅ |
| Node 补环境全链路 ×3（0aq 魔数 / 372~378 / 两次不同） | ✅ |
| 真实请求 ×1（2026-08-20 复测） | ✅ HTTP 200 |

## 验证与实测

- 样例对比：纯 Python 15/15 + --node 18/18 + --live 19/19 全部通过（2026-08-20）
- 真实请求：原项目 2026-06-07 curl 实测 HTTP 200（`0aqW` 前缀）；本仓库 2026-08-20 urllib 复测 HTTP 200，`success:true` 返回真实商品数据
- 失效风险：webpack bundle（subject.js 等）随发版变化，`webpack.js` 的 `var p=i;t()` patch 目标可能变动；签名串如过期需重新抓包提取

## 备注

- RC4 密钥派生（device_id+timestamp → 引擎内密钥）未逆向：纯 Python 输出的 zlib 串直接 base64 **无法通过服务端校验**（缺加密层），`--node` 补环境是全链路唯一途径
- 三层反爬：anti_content（本仓库）/ TLS 指纹（实测 urllib 直连亦可 200）/ headers（Origin + Referer 必须带）
