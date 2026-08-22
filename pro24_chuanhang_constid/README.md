# 川航 — 顶象 ConstID 前端加固: window.sss 自定义字母表 base64 编码器

> 复现对象：`spider research/机票/pro3 四川/`（const_id.js 167KB 混淆 bundle + const_id_server.js JSDOM 服务 + test.ipynb 抓包）· 技术分类：`encrypt`（指纹采集部分属 `env` 补环境）· 状态：✅ 可复现（21/21 通过，2026-08-20 验证）

## 站点与目标

- 站点：`https://www.sichuanair.com/`（四川航空机票）
- 目标接口：`POST rcs.sichuanair.com/udid/c1`（ConstID token 签发，响应 `{"data":"<40字符token>"}`）；搜索接口 `flights.sichuanair.com/3uair/ibe/` 请求头带 `Param`（加密指纹）
- 加密参数：**请求头 `Param` = sss(指纹对象)**；`riskControl/const_id` = 服务端签发的 `token#code`（token = **8 位 hex Unix 秒 + 32 字符**，前缀时间戳已验证 0x6a16ccfe=2026-05-27）

## 技术要点

- 顶象 ConstID SDK，webpack-5 风格打包：46 模块 + 4 张 XOR 编码字符串表（221/186/188/201 项），模块 44 为入口，`window.sss = S` 是调试钩子
- **`sss(r) = 自定义字母表 base64(stringifyJSON(r), reverse(u+f))`**：u=38 字符 + f=27 字符字面量 → 65 字符字母表（末位 `=` 作填充）
- T.encode 是标准 base64 结构（`i>>2`、`&3<<4|>>4`、`&15<<2|>>6`、`&63`），但 `charAt` 越界返回空串 → **非 ASCII 码元 f/c 索引超 64 时输出字符被吞**（"test_1_2_3_输入" 15 码元只出 18 字符，不等长怪癖）
- stringifyJSON 是 json2 风格：`"`、`\x00-\x1f`、`\x7f-\x9f` 转义（映射表 + `\uXXXX` 补零），**反斜杠不在正则里 → 不转义**
- 三个字符串表 XOR 解码器：32432 链式（**非自反**，种子依赖输入）、42045 滚动（自反）、V587 滚动（自反）
- 一句话概括：**指纹对象先 json2 序列化，再经"65 字符字母表 + 越界吞字符"的魔改 base64 得到 Param 头，字母表藏在 u+f 两段字面量拼接倒序里**

## 逆向摘要

- 入口定位：运行时 patch 打包器（`a(a.s=44)` → 暴露 require；`}([` → 暴露工厂数组；外层 IIFE 参数 → 暴露字符串表），定位 mod44 入口（含 S/u/f/y）、mod40（T.encode）、mod3+9（stringifyJSON）
- 还原过程：
  1. 静态拆 mod40：T.encode 逐行对应标准 base64 三分组结构，唯一区别是字母表参数化 + `charAt` 越界空串
  2. JSDOM 实跑原 bundle 捕获 14 组参考输出，逐组对齐 stringify 语义（undefined 省略、整数键升序前置、1e21、控制字符）
  3. 用抓包 972 字符生产 Param 做终极验证：Python 解码 → 完整指纹 JSON（lid/ua/webgl 哈希/GPU/分辨率/时区/appKey）→ 重编码 → **972 字符逐字节相等**
- JS→Python 差异：JS `charAt` 越界→`''`（非 Python 索引越界异常）；`isNaN→'='` 填充；`String(number)` 格式（1e21→`1e+21`、-0→`0`）；`\` 不参与转义

## 复现

```bash
# 依赖: 纯标准库 (json/re/datetime), 零第三方
python main.py   # 14 组 sss 样例 + 生产 Param 双向 + 4 解码器 + 2 token (无网络)
```

| 输入 | 期望输出 |
|------|---------|
| `""` | `B2B=` |
| `"a"` | `B5Z2` |
| `"xOf"` | `B_mcl2B=` |
| `"test_1_2_3_输入"` | `B_RErsRWVYI6hp-Wo2`（2 字符被吞） |
| `{"a":1,"b":"x","c":[1,2]}` | `j6JmBCFePDJ2BCF2jDBTB5V2qETePOJdWz==` |
| `{"a":undefined,"b":1}` | `j6J2BCFeWz==`（undefined 省略） |
| 生产 Param 972 字符（2026-08-19 抓包） | 解码 → 指纹 JSON 25 字段 → 重编码逐字节相等 |

## 验证与实测

- 样例对比：21/21 全部通过（2026-08-20）；期望值 = 原 bundle 经 JSDOM 实跑捕获 + 真实抓包
- 真实请求：原项目 2026-08-19 用 const_id_server.js（JSDOM 补环境跑完整 SDK）实测 token 签发成功（server.log 26 个 token，8-hex 前缀均为 Unix 秒）；本仓库未做网络复测
- 失效风险：u/f 字面量、字符串表、服务端 token 生成若轮换需重新抓包；token 本体由服务端签发，本仓库只复现客户端 Param 编码核心 + token 结构校验

## 备注

- 指纹采集（canvas/webgl 着色器/GPU 参数，模块 32 全是 WebGL 指纹项）必须在浏览器环境执行 → 完整 token 流程用 JSDOM 补环境跑原 SDK（见原项目 const_id_server.js），本仓库聚焦可纯 Python 验证的编码核心
- 解码侧 `sss_decode` 对非 ASCII 内容有损（编码时被吞的字符无法还原），ASCII 指纹 JSON 无损往返
- `verify_with_node.js`（附加，非必需）：JSDOM 实跑原 const_id.js 重新捕获参考值的交叉验证脚本，SDK 更新后用于重采样例
