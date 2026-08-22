# 一嗨租车 — 双向 AES-256-CFB 加密通道（query/body/响应全加密）

> 复现对象：`spider research/其他/pro1 1嗨租车 加密/` · 技术分类：`encrypt` · 状态：✅ 可复现（8/8 通过，2026-06）

## 站点与目标

- 站点：`https://booking.1hai.cn/`（一嗨租车下单页，2026-06-30 实测）
- 加密参数：**URL query 整体加密** + **POST body 加密** + **响应体加密**（Axios 拦截器全量加解密）
- 目标接口：`/bookingApiService/Verify/Step1`（选车）、`/Order/Format/RentDay`、`/User/Detail` 等全部 API；身份认证 JWT Cookie `ehi_f_jwt` → Bearer Token

## 技术要点

- 算法：**AES-256-CFB**（segment 128bit）+ PKCS7 填充 + 标准 Base64 + 字符替换（`+`→`$`、`=`→`*`）+ encodeURIComponent
- 保护类型：全站加密通道（非参数签名）；webpack 打包**无混淆**，密钥硬编码于 module 2780
- 一句话概括：对称加密全通道——拿到 key/IV 即通杀全部接口，难点只是对齐 CryptoJS 的 CFB+PKCS7 组合语义

## 逆向摘要

- 入口定位：DevTools 抓包发现 query/body/响应均为密文（`$`/`*` 特征）→ 源码搜索 `encryptAES` 命中 module 2780 → 回溯 Axios 拦截器（module 4211）确认全量加密
- 还原过程：
  1. 拦截器组装明文：`query = operatorId&platform=1010902&platformSource&timestamp(Y/M/D H:M:S)&原始参数`（qs.stringify），`body = JSON.stringify(...)`
  2. 密钥/IV 硬编码在 module 2780：Base64 32 字节 key + 16 字节 IV（"testing" 环境即生产）
  3. **关键差异**：CryptoJS 在 CFB 模式下显式指定 Pkcs7 填充，而 pycryptodome 的 CFB 不自动填充——需手动 `pad()` 再加密；`segment_size=128` 与 CryptoJS 默认对齐
  4. 编码层：`b64.replace(/=/g,"*").replace(/\+/g,"$")` 后 `encodeURIComponent`（Python 侧 `quote(s, safe="")`）
  5. AES-CFB 固定 IV 无随机性 → **相同明文恒得相同密文**，抓包密文可直接内嵌为期望值
- 备用密钥：`encrypt(plain, t)` 的 `t` 为 truthy 时换 UTF-8 密钥对（本场景未用）；旧接口另有 DES `2f24fks1`

## 复现

```bash
pip install pycryptodome        # 唯一第三方依赖
python main.py
```

| 验证项 | 结果 |
|--------|------|
| 真实抓包密文→明文 ×3（Verify/Step1 / IsAllowExempt / RentDay，2026-06-30） | ✅ |
| 加密确定性 ×1（AES-CFB 固定 IV，同明文同密文） | ✅ |
| 往返 ×3（query 格式 / JSON 含中文 / 特殊字符） | ✅ |
| 完整请求构建 ×1（URL 前缀 + body 密文可解密 + headers） | ✅ |

## 验证与实测

- 样例对比：8/8 通过；3 组密文均来自浏览器实际抓包，解密结果与接口语义吻合（如 `Order/Format/RentDay` → `{"result":"2天"}`）
- 真实请求验证：2026-06-30 用抓包 Cookie 实测 `GET /User/Detail` 成功返回；`/User/Level`、`/Security/User` 因 JWT 过期（有效期 70 分钟）空响应——加密层本身正确

## 备注

- 失效风险：key/IV 若随前端发版更新需重新从 `index.*.js` module 2780 提取；JWT 70 分钟过期需定期刷新 Cookie
- 坑：CFB 模式必须手动 PKCS7（原项目用 CryptoJS 显式 `padding: Pkcs7`）；`$`/`*` 替换的还原顺序（先 `*`→`=` 再 `$`→`+`）；decodeURIComponent 后可能丢 `=` padding，需补位；时间戳格式 `YYYY/MM/DD HH:mm:ss` 带空格（urlencode 后 `%20`）
