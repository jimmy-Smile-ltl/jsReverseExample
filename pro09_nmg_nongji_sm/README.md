# 内蒙古农机购置补贴 — 国密 SM4-ECB + SM3 + RSA-512 密钥护送

> 复现对象：`spider research/其他/pro18 内蒙古农机补贴 SM/` · 技术分类：`encrypt` · 状态：✅ 可复现（8/8 通过，2026-06 实测）

## 站点与目标

- 站点：`http://111.56.142.13:18088/subsidyOpen`（内蒙古农机购置补贴公示系统，2026-06 实测）
- 加密参数：请求头 `sign` / `timestamp` / `parameter`（三件套均为 **SM4-ECB 密文 hex**），另有固定 `source`
- 目标接口：`/api/api/loginSidePageEDE/getPurchaseOfAgriculturalMachinery`（补贴列表）、`getPurchaseSubsidyOpenTopMsg`（汇总）

## 技术要点

- 算法：**SM4-ECB**（国密对称）+ **SM3**（国密哈希）+ **RSA-512** 私钥引导 SM4 key
- 保护类型：国密全家桶 + 签名链；SM4 key 由客户端内置 RSA 私钥解密（固定密钥，非每次会话）
- 一句话概括：签名 = SM3(排序查询串 + 固定 key 盐) 大写后 SM4 加密，难点在 JS 的空值过滤与排序语义

## 逆向摘要

- 入口定位：抓包见 `sign/timestamp/source/urlprefix` 四头 + body `{"parameter": hex}` → 源码搜索 `source` 命中 SM4/SM3/RSA 常量
- 还原过程：
  1. 密钥引导：`ENCRYPTED_SM4_KEY_B64` 用硬编码 RSA-512 私钥（PKCS#8 DER）PKCS#1 v1.5 解密 → 得 32 字符 hex 串 → `bytes.fromhex` 得 16 字节 SM4 key（**hex 串本身再解码一层**，易踩坑）
  2. `sign`：请求参数（含 timestamp）key 字母排序 → **过滤空值**（`None`/`""`/`0`，对应 JS `if(val)`）→ `encodeURIComponent(key)=value` 用 `&` 连 → 拼 `&key=API_KEY` → SM3 → **大写** → SM4 加密
  3. `timestamp` = SM4(毫秒字符串)；`parameter` = SM4(JSON.stringify 无空格)
  4. RSA 私钥硬编码于客户端，本复现提取 n/d 后**纯 Python `pow(c, d, n)` 解密**，不依赖 cryptography
- 数据来源：原项目 `spider.py` 完整模块（常量 + 流程逐行对照）

## 复现

```bash
pip install gmssl                 # 唯一第三方依赖 (SM4 + SM3)
python main.py
```

| 验证项 | 结果 |
|--------|------|
| RSA 引导 ×1（解密 SM4 key = 期望 hex 串） | ✅ |
| SM4 往返 ×2（中文 JSON / 特殊字符） | ✅ |
| sign 自洽 ×1（解密 sign 与重算 SM3 期望一致）+ 确定性 ×1 | ✅ |
| timestamp 往返 ×1 / parameter 往返 ×1 | ✅ |
| 请求结构 ×1（headers 四件套 + body） | ✅ |

## 验证与实测

- 样例对比：8/8 通过；sign 自洽验证采用"解密→重算 SM3→比对"闭环（原始密文未留存）
- 真实请求验证：原项目 2026-06 实测列表/汇总接口返回 `code:200`，`_decrypted` 解密出补贴明细

## 备注

- 失效风险：RSA 私钥/SM4 key/API_KEY 均为客户端内置常量，前端发版才可能更换；站点为 IP 直连，需注意请求时区与 TLS 校验（原实现 `verify=False`）
- 坑：SM3 输入为 UTF-8 字节列表（gmssl 接口）；排序过滤需同时排除 `0`（JS truthy 语义）；`urlprefix` 为空串但必须出现在 header 中
