# WIPO 全球商标数据库 — 非标准 AES-416 (13 words / 19 轮) 手写实现 + PKCE S256

> 复现对象：`无限集数/其他/全球商标数据库/`（CryptoJS.js 混淆 bundle + 解码.js + auth.js + spider.py + test.ipynb）· 技术分类：`encrypt` · 状态：✅ 可复现（11/11 通过，2026-08-20 验证）

## 站点与目标

- 站点：`https://brands.wipo.int/`（WIPO 全球商标搜索）
- 目标接口：`POST /brands/search/api/v1/search`，header 带 `hashsearch`（UUID）与 `Authorization: Bearer`（ForgeRock OAuth2）
- 加密参数：**响应 `data` 字段 = base64 AES 密文**（请求侧无参数加密）
- 前置链路：OAuth2 ForgeRock `/am/oauth2/.../authorize` → PKCE S256 challenge → access_token → hashsearch UUID

## 技术要点

- **非标准 AES**：key = 静态 16 字符 + hashsearch UUID 36 字符 = **52 字节 (416 bit)**；CryptoJS 4.x 广义 key schedule：`r = sigBytes/4`=13 words、`nRounds = 6 + r`=**19 轮**（标准 AES-128/256 为 10/14 轮）、schedule 80 words、Rcon `B=[0,1,2,4,8,16,32,64,128,27,54]`（index≥11 → JS `undefined<<24`=0）、且 `r>6` 时每轮 `o%r==4` 的 word 额外做一次 SubWord
- 模式：ECB + Pkcs7（`CryptoJS.AES.decrypt(de, key, {mode: ECB})`）
- pycryptodome 不支持非标准 key 长度 → **纯 Python 手写 AES**（S-box 用 GF(2^8) 乘法逆元 + 仿射变换程序化生成）
- 一句话概括：**搜索页数据全量加密，密钥被拆成"静态前缀 + 请求头 UUID"两段拼接，配合 416-bit 非标轮数让标准库全部失效**

## 逆向摘要

- 入口定位：spider.py 运行时调解密函数；解码.js 是解密最小复现（`decrypt(de)` 单函数）；CryptoJS.js 为混淆 bundle（内嵌 AES + node crypto 适配层）
- 还原过程：
  1. 从 bundle `_doReset` 源码逐行反推广义 key schedule（nRounds=6+r、80 words、o%r==4 的 SubWord 分支）
  2. 用 test.ipynb cell10 的 AES-128 向量（"Hello, World!" → `cc504ae9...`）锁定轮函数正确性（期间发现状态装载必须按 FIPS-197 列主序 `s[r][c]=in[r+4c]`）
  3. 52 字节 key 解密真实密文 → sha256 与 node 实跑一致 + **重加密与原密文逐字节相等**（ECB 确定性，最强等价证明）
  4. PKCE：auth.js `io(60)` 生成 verifier（字母表 `0-9A-Za-z+/`），`qi()` = urlsafe_b64(SHA256) 去 `=`
- JS→Python 差异：标准 AES 的 key schedule 对 4 字节 word 数固定的 key 才成立，这里必须按源码推广；JS 数组越界 `undefined<<24`=0 用 `RCON[i] if i<len else 0` 模拟；字节序全大端（`int.from_bytes(..., "big")`）

## 复现

```bash
# 依赖: 纯标准库 (base64/hashlib/json/secrets), 零第三方
python main.py   # 11 项: S-box/key schedule/解密/重加密/PKCE (无网络)
```

| 输入 | 期望输出 |
|------|---------|
| key=`8?)i_~Nk6qv0IX;2`(16B) + "Hello, World!"（test.ipynb cell10 向量） | `cc504ae98934a33c5f2c001962deb730` |
| FIPS-197 向量 key=00..0f + pt=0011..eeff | `69c4e0d86a7b0430d8cdb78070b4c55a` |
| 52B key + 真实密文（samples.json，2024-11 抓包，12304B） | sha256 `055333433ba15f3a...`，numFound=66699623，start=30，首条 "A BETTER HEALTH JOURNEY" NZ502024001278899 |
| 解密出的明文重加密 | 与原密文**逐字节相等**（769 块） |
| PKCE verifier `hTiGncH4+...`（node 实跑捕获） | challenge `4iUUmGboyU3QGbI1...` |

## 验证与实测

- 样例对比：11/11 全部通过（2026-08-20）；期望值 = 原 bundle node 实跑捕获（sha256）+ 原项目留存向量（cell10）+ 官方 FIPS-197 向量
- 真实请求：原项目 2024-11 实爬 WIPO 商标搜索成功（含 OAuth2 授权流）；本仓库未做网络复测（token/UUID 需实时授权流，超出逆向核心范围）
- 失效风险：静态 key 前缀、UUID 来源（hashsearch header）若服务端轮换需重新抓包；解密逻辑与 CryptoJS 版本强绑定（bundle 是 4.x 风格广义 schedule）

## 备注

- S-box 不依赖硬编码表：GF(2^8) 逆元（平方-乘 a^254）+ AES 仿射变换程序化生成，5 个标准值抽查 + FIPS 向量 + 19 轮真实解密三重验证
- 解密时若 UUID 变了（每次请求 header 不同），只需换 `UUID_HEADER` 常量——这是"密钥由响应侧字段决定"的设计：响应必须用**同一请求**的 hashsearch 才能解开
