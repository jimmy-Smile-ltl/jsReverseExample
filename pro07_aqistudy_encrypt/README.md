# 中国空气质量在线监测分析平台 — 双重加密 + 混淆（AES→DES 解密链）

> 复现对象：`spider research/其他/pro21 中国空气质量在线监测分析平台 混淆 加密/` · 技术分类：`encrypt` `obfuscate` · 状态：✅ 可复现（10/10 通过，2026-06 实测）

## 站点与目标

- 站点：`https://www.aqistudy.cn/`（2026-06-29 实测北京/上海/广州实时数据接口）
- 加密参数：POST `/apinew/aqistudyapi.php` 的 body 参数名固定为 `h1zlb1QoZ`（值为 base64）
- 目标接口：`GETDETAIL`（实时数据）、`GETCITYWEATHER`（天气）；响应整体加密

## 技术要点

- 算法：请求侧 `MD5(appId+method+ts+clienttype+JSON)` 签名 + Base64；响应侧 **Base64→AES-CBC→Base64→DES-CBC→Base64→JSON** 双重解密链
- 保护类型：JS 混淆（函数名混淆为 `pvkWB5TRrM9kT5` / `d6o2KJrVnYKBvdlc6mTrx4`）+ 参数签名
- 一句话概括：最难的不是算法，而是**密钥派生**——MD5 的 hex 串按 UTF-8 字节当 key/iv 用，不是 hex 解码

## 逆向摘要

- 入口定位：抓包见参数名 `h1zlb1QoZ` → 源码搜索该名 → 定位加密/解密函数 → 逆出密钥派生
- 还原过程：
  1. 原始密钥 4 个常量硬编码在 JS：`a5slhqEdLos7hvjr`（AES key）/ `bhb9eTODiif32jv0`（AES iv）/ `hXenRdbrF1iqaMLr`（DES key）/ `xAWozmps3eqYftMA`（DES iv）
  2. **核心坑**：`MD5(常量)` 得到的 32 位 hex 串再按**字符串 UTF-8 字节**作 key/iv——AES key=`[16:32]`、iv=`[0:16]`，DES key=`[0:16]` 截 8 字节、iv=`[24:32]`（hex 解码则全错）
  3. 响应：AES-CBC 解密 → 明文是 Base64 → DES-CBC 解密 → 明文还是 Base64 → JSON
  4. 请求：对象按 key 排序后 `JSON.stringify`（无空格）拼入 secret 计算链，再与 appId/method/timestamp/clienttype 一起 JSON 后 Base64
  5. **2026.06 站点升级**：请求加密层移除（旧版多一层 AES-CBC），appId 由旧值更换为 `0e5df784c9068129938846e4fd750fdd`；响应链路不变
- 数据来源：原项目 `aqistudy_crypto.py` 完整模块 + `REVERSE_REPORT.md`（2026-06-29 实测记录）

## 复现

```bash
pip install pycryptodome        # 唯一第三方依赖
python main.py
```

| 验证项 | 结果 |
|--------|------|
| 密钥派生 ×4（AES key/iv、DES key/iv 期望值内嵌） | ✅ |
| 解密链往返 ×3（真实响应 JSON 结构，构造→还原） | ✅ |
| 请求加密确定性 ×2（固定 timestamp 两次一致） | ✅ |
| 请求结构 ×1（appId/method/timestamp/clienttype/object/secret 六字段） | ✅ |

## 验证与实测

- 样例对比：10/10 通过；密钥派生期望值与 JS 计算流程逐值一致
- 真实请求验证：原项目 2026-06-29 实测三城市（北京/上海/广州）GETDETAIL 请求解密成功，链路与本站一致
- 说明：实战响应密文未留存，解密链验证采用"构造→还原"自洽方式；按 README 抓包步骤可复测

## 备注

- 失效风险：appId 已换代一次（2026.06），密钥常量随前端发版可能更新；响应链的 `JSON.stringify` 需注意无空格格式
- 坑：hex 串按 UTF-8 字节使用（非 hex 解码）；`sorted(obj)` 需递归处理嵌套对象（本复现取顶层排序，嵌套结构与实战一致即可）；Python `time.time()*1000` 取整与 JS `Date.now()` 对齐
