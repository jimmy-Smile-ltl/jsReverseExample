# 网易云音乐 — weapi 参数加密（双层 AES-128-CBC + RSA-1024）

> 复现对象：`spider research/其他/pro27 网易云 参数加密/` · 技术分类：`encrypt` · 状态：✅ 可复现（7/7 通过，2026-06-30 实测）

## 站点与目标

- 站点：`https://music.163.com/`（2026-06-30 实测）
- 加密参数：POST body 的 `params` + `encSecKey`（URL 带 `csrf_token`，取自 Cookie `__csrf`）
- 目标接口：`/weapi/song/enhance/player/url/v1`（歌曲播放 URL）、`/weapi/v6/playlist/detail`（歌单）

## 技术要点

- 算法：**双层 AES-128-CBC**（固定密钥 `0CoJUm6Qyw8W8jud` 加密后再用随机密钥加密）+ **RSA-1024** 加密随机密钥
- 保护类型：经典"对称密钥换发"方案——每请求随机 AES 密钥，RSA 公钥护送
- 一句话概括：算法教科书级，难点全在**对齐 JS 语义**：CryptoJS 的 KDF 坑、RSA 零填充 + 小端字节序

## 逆向摘要

- 入口定位：Console 搜索 `encSecKey` 命中全局函数 `window.asrsea` / `window.ecnonasr` → 解混淆 core.js 还原三层流程
- 还原过程：
  1. `asrsea(data, exp, mod, fixedKey)`：随机 16 位密钥 `a(16)` → 固定密钥 AES → 随机密钥 AES → RSA
  2. **坑 1**：CryptoJS 传字符串给 AES 会走 OpenSSL KDF 派生密钥，必须 `CryptoJS.enc.Utf8.parse()` 显式转 WordArray——Python 直接 `key.encode()` 即等价
  3. **坑 2**：JS 的 `encryptedString` 是**零填充**（补 `\x00` 到 126 字节），非 PKCS#1 v1.5，标准 RSA 库不可用，必须 `pow(msg, e, n)` 裸算
  4. **坑 3**：JS BigInt digit 为 little-endian 16-bit 字 → Python `int.from_bytes(padded, 'little')`；密文 hex 不定长（无前导零）
  5. **坑 4**：`JSON.stringify` 无空格且保留中文 → `json.dumps(separators=(',', ':'), ensure_ascii=False)`
- `ecnonasr` 变体：纯 RSA（`data+suffix`），少数端点用

## 复现

```bash
pip install pycryptodome        # 唯一第三方依赖 (RSA 用 pow 裸算, 无需 rsa 库)
python main.py
```

| 验证项 | 结果 |
|--------|------|
| 浏览器验证期望值 ×3（第一层 AES / 第二层 AES / RSA，固定密钥，2026-06-30） | ✅ |
| 完整加密往返 ×1（含中文关键词 + 嵌套字段，解密还原） | ✅ |
| URL 编码 body ×1（params=...&encSecKey=...） | ✅ |
| 真实抓包结构 ×2（params 合法 base64 + 16 字节对齐；encSecKey 恒 256 hex） | ✅ |

## 验证与实测

- 样例对比：7/7 通过；三组期望值逐字节与浏览器计算结果一致
- 真实请求验证：原项目 2026-06-30 API 测试 HTTP 200（`{"code":200,"data":[...]}`）；歌曲 URL 需 VIP Cookie（加密本身正确）

## 备注

- 失效风险：核心 JS `core_*.js` 文件名带 hash 随版本更新，但 `window.asrsea` 流程多年未变；`__csrf` Cookie 需会话级获取
- 坑：RSA 若用 `pycryptodome`/`rsa` 库会因 PKCS#1 padding 不一致失败；AES 每层 key 不同（内层固定外层随机），解密必须外层先解
