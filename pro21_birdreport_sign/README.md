# 中国观鸟记录中心 — 请求签名 (RSA-1024 分块 + MD5) + 响应 AES-128-CBC 解密

> 复现对象：`无限集数/其他/观鸟记录中心/`（spider_报告.py + before_ajax.js + 解码.js + detail.js）· 技术分类：`encrypt` · 状态：✅ 可复现（13/13 通过含真实请求，2026-08-20 验证）

## 站点与目标

- 站点：`https://www.birdreport.cn/`（API：`https://api.birdreport.cn/`）
- 目标接口：`POST /front/record/activity/search`（报告列表）、`POST /front/record/activity/taxon`（鸟种记录）
- 加密参数：**body = RSA 密文**；headers 带 `sign` / `timestamp`（字符串）/ `requestid`
- 响应：`data` 字段为 base64 密文，AES-128-CBC 解密后是 JSON 数组

## 技术要点

- 请求：RSA-1024 / PKCS1v1.5，117 字符/块分块加密（hex 拼接后 base64）作 body
- 签名：`sign = MD5(明文排序JSON + requestId + timestamp)`——**明文参与 MD5，不是密文**（xhr.js 抄录版把密文参与签名是笔误，实测被拒"无效签名"）
- 响应：AES-128-CBC，key `C8EB5514AF5ADDB94B2207B08C66601C`、iv `55DD79C6F04E1A67`、Pkcs7
- 一句话概括：**参数先 encodeURIComponent 转 %XX 形态 → 键升序 → 紧凑 JSON → RSA 加密发 body + MD5 发 header**

## 逆向摘要

- 入口定位：spider.py 三个 execjs 环境分别跑 province.js/解码.js/before_ajax.js；与站点现行 jqueryAjax.js 的 `$.ajaxSetup({beforeSend})` 逐字比对一致（2026-08-20 抓取）
- 还原过程：
  1. `param()` 每对 k/v encodeURIComponent 后 `&` 连接 → `dataTojson()` 切回 dict（**值保持 %XX 形态**）→ `sort_ASCII` 键升序 → `JSON.stringify` 紧凑序列化
  2. `encryptLong`：117 字符/块 → PKCS1v1.5（0x00 0x02 随机 PS 0x00 数据）→ hex 拼接 → base64；注意本站点实现是**逐字符 UTF-8**（非 JSEncrypt 老版 UTF-16BE）
  3. `sign = MD5(json_str + requestId + timestamp)`，timestamp 是毫秒字符串
- JS→Python 差异：`encodeURIComponent` safe 集 `!~*'()` 需用 `urllib.parse.quote(..., safe="!~*'()")` 对齐；JSON 键序用 `sorted()`；requestId 任意 32 位 hex（uuid4().hex 实测可用）

## 复现

```bash
# 依赖: pycryptodome (pip install pycryptodome)
python main.py         # 签名链 + AES 解密 + RSA 结构 + 详情 URL (无网络, 12 项)
python main.py --live  # +1 项: 真实请求 -> RSA body + sign headers -> HTTP 200 -> AES 解密
```

| 输入 | 期望输出 |
|------|---------|
| {page,limit,province:四川,...} + rid + ts（2026-08-20 抓包） | 中间 JSON `{"endTime":"","limit":"50","page":"1","province":"%E5%9B%9B%E5%B7%9D",...}` + sign `34988ec78cf4...` |
| MD5("false"+rid+ts)（2024-12-17 调试样例） | `f786c300dffb34c3ea9cd89745486c9b` |
| AES 密文（2024-12-17 真实响应） | 地址"云南省保山市隆阳区蒲缥镇"、reportId `e6d33531-...`、username ptarmigan |
| RSA 结构（117/118/234/235/300 字符） | 分块数 = ceil(n/117)，128B/块，base64 长度公式 |
| detail.js 详情 URL | param=Base64(JSON)，sign=**MD5("")** 固定 `d41d8cd9...`（calcMD5 传对象返回空串，服务端不校验） |

## 验证与实测

- 样例对比：12/12 通过（2026-08-20）
- 真实请求：`--live` HTTP 200 `{code:0, count:54886}`，50 行数据 AES 解密成功（首条 end_time=2026-08-19 21:45，2026-08-20 实测）；缺 Referer/UA 会 403
- 失效风险：AES key/iv 若轮换需重新抓包（aes.util.js 另有混淆密钥串，实测对当前响应无效，疑似登录等其他接口用）；频繁访问触发 4 位数字 kaptcha 验证码（需代理池）

## 备注

- xhr.js 的 `getHeaders` 是笔误调试版（sign 算在密文上），before_ajax.js 才是正确版——还原时两个文件都留在了原项目
- 验证码接口 `GET /front/code/visited/generate?timestamp=` + `POST /front/code/visited/verify`（{"code":"4位数字"}）本身无需签名；OCR 识别未成功，靠代理池规避
