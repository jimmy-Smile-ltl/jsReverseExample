# 酷狗音乐 — 登录加密：signature + RSA-1024 NoPadding + 定制 CryptoJS AES

> 复现对象：`spider research/其他/pro23 酷狗音乐 登录 滑块验证码 wasm/` · 技术分类：`encrypt` · 状态：✅ 可复现（8/8 通过，2026-06-29 实测）

## 站点与目标

- 站点：`https://www.kugou.com/`（短信验证码登录，2026-06-29 实测）
- 加密参数：URL query `signature`、body `pk`（RSA 密文）/ `params`（AES 密文）/ `mid` / `uuid`
- 目标接口：`POST gateway.kugou.com/v8/send_mobile_code`、`verifyservice.kugou.com/v3/get_verify_info`、`loginservice.kugou.com/v2/login_by_verifycode`

## 技术要点

- 算法：**MD5 签名**（salt 包裹排序参数 + JSON body）+ **RSA-1024 NoPadding**（payload 反转 + little-endian）+ **定制 AES-128-CBC**（CryptoJS 自有实现，非标准）
- 保护类型：三件套组合签名；核心 JS `kguser.v2.min.js`（90KB）；验证码环节 135KB WASM 生成 `sid`/`edt`
- 一句话概括：signature 与 RSA 纯 Python 可复现，**AES 是坑王**——标准 AES 输出被服务器拒绝，必须跑提取的 CryptoJS 原始模块

## 逆向摘要

- 入口定位：XHR 断点搜 `send_mobile_code` 命中 `GetSmsCode` → `getInterFaceKguser` 中见 salt 拼接签名 → `RSA.encrypt` 反混淆见字节布局
- 还原过程：
  1. `signature = MD5(salt + 排序key=value无分隔 + JSON body + salt)`，大写；body 为 falsy 时整段省略
  2. `pk`：明文 JSON 反转放末尾 → 前导零补 128 字节 → **little-endian** 解释为整数 → `pow(m, 0x10001, n)` → 256 hex
  3. **AES 对照实验**（固定 key `5SO2VCRF8O81PJH3` + 固定明文）：CryptoJS 原始模块 `d4f624c0...`（服务器接受 ✓）vs 标准 AES `bd78094a...`（拒绝 ✗）；已排除 AES-256/ECB/IV 变体全部假设 → 直接从 `kguser.v2.min.js` offset 5969~27077 **提取 21KB 纯 JS CryptoJS 模块**（`kugou_aes_module.js`）Node 原生运行
  4. `mid = MD5(uuid)`，uuid 与 mid 同值；dfid 取 `kg_dfid` cookie
- 边界：腾讯 TX Captcha（v_type=23 滑块）→ 归 `../captcha_example/`；WASM `sid`/`edt` 未深入（环境检测严格）

## 复现

```bash
# 依赖: Python 标准库 (0 第三方); --node 交叉验证需本机 node
python main.py            # 5 项纯 Python 验证
python main.py --node     # 追加 3 项: CryptoJS 模块 AES + Node RSA 交叉 + 现场生成 params
```

| 验证项 | 结果 |
|--------|------|
| RSA 固定明文期望 ×1（2026-06-29 与浏览器逐位一致） | ✅ |
| signature 结构 ×2（固定参数期望 + body 参与签名） | ✅ |
| mid=MD5(uuid) ×1 / 完整请求组装 ×1 | ✅ |
| --node: 定制 AES 与浏览器实测一致 ×1（固定 key） | ✅ |
| --node: RSA 独立实现交叉 ×1 + 现场生成 params ×1 | ✅ |

## 验证与实测

- 样例对比：8/8 通过；AES 期望值来自原项目 2026-06-29 三方对照实验（浏览器 CryptoJS ✓），RSA 期望值与浏览器逐位一致
- 真实请求验证：原项目签名算法对真实抓包验证 MATCH（`signature=0D92E57B0936361C5C56ECE093B03BAF`）；send_mobile_code 返回 `error_code:20028`（触发滑块，属预期流程）
- 说明：README 中抓包 body 的 pk/params 被截断，无法内嵌该条完整签名样例；结构验证用固定参数 + Node 双实现交叉

## 备注

- 失效风险：salt/公钥随前端发版可能更换；`kguser.v2.min.js` 文件名带版本号；验证码环节需第三方识别
- 坑：**payload 反转 + little-endian**（不是大端）；RSA 密文 256 hex 需 `zfill`；signature 中 URL 参数不包含 signature 自身；AES 必须用提取模块（Python/OpenSSL 标准实现全错），`AES.encrypt(plaintext, key)` 第二参数可固定 key 便于比对
