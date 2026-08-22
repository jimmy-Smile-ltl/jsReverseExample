# 拉钩网 — 职位搜索加密链: AES-256-CBC + RSA-2048 保护 AES Key + X_HTTP_TOKEN

> 复现对象：`无限集数/招聘网站/拉钩/`（拉钩解码.js + 拉钩.py + 拉钩.ipynb）· 技术分类：`encrypt` · 状态：✅ 可复现（21/21 通过，2026-08-20 验证）

## 站点与目标

- 站点：`https://www.lagou.com/`（职位搜索，需 `user_trace_token` cookie）
- 目标接口：`POST https://www.lagou.com/jobs/v2/positionAjax.json`，body `{data: AES密文}`，响应 `data` 字段 AES 密文
- 加密参数：`X-S-HEADER`（请求体 SHA256 签名密文）、`X_HTTP_TOKEN`（cookie 派生的反向 token）、`traceparent`（W3C 格式）
- 前置链路（未复现）：AES Key 经 RSA 加密后 POST `gate.lagou.com/system/agreement` 激活 → `X-K-HEADER`；`__lg_stoken__` 来自 302 挑战页的混淆 JS

## 技术要点

- 请求/响应：AES-256-CBC，key = 32 字符随机串（字母表 `ABCD...+/=`），iv 固定 `c558Gq0YQK2QUlMc`，Pkcs7，base64 输出
- Key 保护：JSEncrypt RSA-2048/PKCS1v1.5 加密 32 字符 AES Key → 344 字符 base64
- `X-S-HEADER = AES({originHeader:"{\"deviceType\":1}", code: SHA256({deviceType:1}+url+body).toUpperCase()})`
- `X_HTTP_TOKEN = reverse( MD5("HTTP_JS_KEY"+user_trace_token)[:16] + ts秒 + [16:32] )`
- 一句话概括：**双密文双签名——AES 保数据、RSA 保 AES Key、SHA256 保请求完整性、MD5+reverse 防 token 直读**

## 逆向摘要

- 入口定位：抓包对比明文请求与密文 body，`getRequestData` 即 AES 加密；`getXSHeader` 中 SHA256 拼接 `u`（url）参数实为 undefined 时 concat 出字面 `"undefined"`
- 还原过程：
  1. `Rt/It`：CryptoJS AES-CBC，iv 在 JS 中写死，输出 `t.toString()` = base64
  2. `jt`：SHA256(`{"deviceType":1}` + url + 紧凑 JSON body) 大写 → 包进 JSON 再 AES
  3. `getXHttpToken`：OB 字符串表 59 元素 shift 331 次（331%59=36）后解码出 `HTTP_JS_KEY`/`user_trace_token`；ts = `Math.floor(Date.now()/1000)`
  4. `E(t)`：Uint8Array(16) 随机 + 256 项 hex 表 → `substr(0,t)` → traceparent 32/16 hex
- JS→Python 差异：CryptoJS `.toString()` = 标准 base64；`JSON.stringify` 紧凑序化用 `json.dumps(separators=(",",":"), ensure_ascii=False)`（`全国` 必须 UTF-8 而非 `\u` 转义）；Pkcs7 补位数=补字节值

## 复现

```bash
# 依赖: pycryptodome (pip install pycryptodome)
python main.py   # X-S-HEADER×2 + token×3 + 请求加密 + 响应解密 + RSA 结构 (纯 Python, 无网络)
```

| 输入 | 期望输出 |
|------|---------|
| aesKey=`dgHY1qVeo/...` + 测试块 originalData + u=undefined（2024-07-17 测试块） | X-S-HEADER `NeeOlLq93FMl0Xzi79Fr4...`（node 实跑捕获） |
| 同上 + 真实 url `https://www.lagou.com/jobs/v2/positionAjax.json` | X-S-HEADER `NeeOlLq93FMl0Xzi79Fr4A3PQF57CqoaROkcM8N9wmObOO...` |
| cookie `user_trace_token=20220307181843-...` + ts=1787157649 | `e5ab78d92f389422946751787106351df7c5441dab` |
| 测试块 originalData → getRequestData | `4vkQ2vHW22A7cVp2Z0Ke8gnpOAaW7X2h...` |
| 真实响应密文（samples.json，2024-07-17 抓包） | 明文 sha256 `5d75cc6922d59582...`，首条"高级Python工程师@北京木瓜移动科技股份有限公司 20k-40k"，totalCount=360772 |

## 验证与实测

- 样例对比：21/21 全部通过（2026-08-20）；期望值 = 原 JS + 真实 crypto-js/jsencrypt 经 node 实跑捕获，token 另有两组不同 ts 的实跑值交叉验证
- 真实请求：原项目 2024-07-17 实爬 9 页全国 Java 岗位成功（含 __lg_stoken__/X-K-HEADER 挑战链）；本仓库未做网络复测（完整链路需先过挑战，超出逆向核心范围）
- 失效风险：iv、RSA 公钥、`HTTP_JS_KEY` 拼串若轮换需重新抓包；`__lg_stoken__` 为 302 挑战页动态 JS，未收录（见拉钩.py get_lg_stoken）

## 备注

- 测试块 `getXSHeader(aesKey, originalData)` 只传 2 参 → u=undefined，JS concat 出 `"undefined"` 参与 SHA256——已按原样复现并单独成组样例
- `X-K-HEADER`（gate 激活返回的 secretKeyValue）与 `x-anit-forge-*` 为服务端签发值，不属于 JS 加密核心
