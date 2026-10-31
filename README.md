# JS 逆向复现集 (jsReverseExample)

从实战爬虫项目中提取的 **JS 逆向核心复现**：每个项目最小化呈现「加密入口 → 算法还原 → 可运行验证」的完整链路。原则：**最简化、可复现、文档清晰**——去掉工程化外壳（数据库、断点续爬、代理、日志），只保留逆向技术本身。

> ⚠️ **合规声明（必读）**：本仓库仅用于**个人学习、学术研究与授权安全测试**。所涉网站、SDK、数据的版权归其原始权利人所有；抓包样例均为已过期的测试向量。请遵守目标站点的服务条款与适用法律，禁止用于商业爬取或任何恶意用途。详见 [LICENSE](LICENSE)。

## 快速开始

```bash
# 每个项目独立可跑，一条命令验证
cd pro07_aqistudy_encrypt && py main.py    # 示例：10/10 通过（Linux/macOS 用 python）
```

- 运行**不依赖网络**：所有样例为内置测试向量，输出即验证结果
- 依赖：Python 标准库优先，第三方 ≤ 2 个（见各项目 README）
- 真实请求验证与抓包方法写在各项目 README「验证与实测」章节

## 项目清单

### 参数加密

| 编号 | 项目 | 技术点 | 状态 |
|------|------|--------|------|
| [pro12](pro12_kugou_login_crypto/) | 酷狗音乐 登录加密 | MD5 salt 签名 + RSA-1024 NoPadding（反转+小端）+ 定制 CryptoJS AES | ✅ 8/8 通过 |
| [pro10](pro10_yingdong_ws_aes/) | 颍东先锋网 网盟 WAF | AES-128-CBC 会话密钥派生（etag→priKey 链）+ WebSocket 指令帧协议 | ✅ 8/8 通过 |
| [pro09](pro09_nmg_nongji_sm/) | 内蒙古农机补贴 国密 | SM4-ECB + SM3 签名 + RSA-512 私钥引导 SM4 key | ✅ 8/8 通过 |
| [pro08](pro08_wangyiyun_weapi/) | 网易云音乐 weapi | 双层 AES-128-CBC + RSA-1024 零填充小端 | ✅ 7/7 通过 |
| [pro07](pro07_aqistudy_encrypt/) | 空气质量平台 双重加密 | MD5 签名 + Base64→AES-CBC→DES-CBC 解密链 | ✅ 10/10 通过 |
| [pro06](pro06_1hai_aes/) | 一嗨租车 全站 AES 通道 | AES-256-CFB + PKCS7 + 自定义 Base64 | ✅ 8/8 通过 |
| [pro05](pro05_xueqiu_md5_1038/) | 雪球网 md5__1038 签名 | SHA1 截取 + 随机 XOR + 环境 bit + 自定义 LZW（纯算/Node 双实现） | ✅ 13/13 通过（Node 逐字节） |
| [pro04](pro04_shzz_slide_abc/) | 社会组织平台 滑块 a/b/c | RSA-1024 + 双重 base64 + OpenCV 缺口识别 | ✅ 10/10 通过 |
| [pro18](pro18_pinduoduo_anticontent/) | 拼多多 anti_content | 22 collector 序列化 + zlib level 6 + budget 扰码 base64；纯算法 + 原版引擎双路线 | ✅ 20/20 通过（Node 23/23） |
| [pro26](pro26_nanhang/) | 南航 机票搜索 encryptArgs | RSA+RC4 请求加密（未逆向，浏览器自动化绕过）+ requestId 参数模板还原 | 🔒 3/3 通过 |
| [pro27](pro27_cls_sign/) | 财联社电报 sign | 参数大写排序 + 递归序列化 + SHA1→MD5 双重哈希 | ✅ 5/5 通过 |
| [pro28](pro28_toutiao_abogus/) | 今日头条 a_bogus | bdms VM 还原为纯算法（148 字符）+ 旧版 Node 补环境备份 + 线上实测 | ✅ 7/7 通过（Node 10/10） |
| [pro20](pro20_wipo_aes416/) | 全球商标数据库 CryptoJS | CryptoJS AES 完整还原（S-box/key schedule）+ 解密/重加密 + PKCE | ✅ 11/11 通过 |
| [pro21](pro21_birdreport_sign/) | 观鸟记录中心 | 签名链 + AES 解密 + RSA 结构 + 详情 URL 派生 | ✅ 13/13 通过 |
| [pro22](pro22_baidu_index/) | 百度指数 数据解密 | 单表替换密码（真实三元组对照） | ✅ 7/7 通过 |
| [pro23](pro23_lagou_crypto/) | 拉钩 X-S-HEADER | X-S-HEADER 签名 + token 加密 + 请求加密/响应解密 + RSA 结构 | ✅ 21/21 通过 |

### 混淆还原 / 反调试

| 编号 | 项目 | 技术点 | 状态 |
|------|------|--------|------|
| [pro17](pro17_aiqicha_abclite/) | 爱企查 ABCLite-2061 | `\xHH` 双重转义字符串还原 + eval 劫持栈分析反调试 + 7 类指纹检测 | ✅ 42/42 通过 |
| [pro13](pro13_yinghua_jsjiami/) | 樱花动漫 jsjiami v7 | 自定义 base64（小写字母表）+ RC4 字符串表 + 5 层反调试判定 | ✅ 29/29 通过 |
| [pro29](pro29_mps_ast_encode/) | 公安部 编码链 + AST 教学 | encode64/t/u/a 编码链复现 + Babel AST 反混淆教学 demo | ✅ 5/5 通过 |

### WAF 逆向

| 编号 | 项目 | 技术点 | 状态 |
|------|------|--------|------|
| [pro14](pro14_landchina_antidebug/) | 中国土地市场网 CloudWAF | 渐进式行为画像 + disable-devtool 七检测器 + MD5 Hash 头 | ✅ 34/34 通过 |
| [pro01](pro01_jiasule_521/) | 加速乐 521 挑战 | `go()` 数据暴力双循环 + 标准 hash 掉包 | ✅ 3/3 通过 |
| [pro02](pro02_shyq_yunsuo/) | 云锁 WAF 三步挑战 | 字符级 hex 编码 + `security_verify_data` cookie 链 | ✅ 4/4 通过 |
| [pro03](pro03_opticsjournal_acw/) | 阿里云 WAF `acw_sc__v2` | 固定置换表 unsbox + 固定 key 异或 | ✅ 4/4 通过 |
| [pro32](pro32_oatd_cloudflare/) | oatd.org Cloudflare Turnstile 应对 | cf_clearance Cookie 刷新五方案 + Turnstile DOM 状态机 + 拟人贝塞尔轨迹 | ✅ 13/13 通过（真实刷新需浏览器） |

### WASM / VM 保护

| 编号 | 项目 | 技术点 | 状态 |
|------|------|--------|------|
| [pro16](pro16_gdtv_wasm/) | 荔枝网 gdtv API 认证 | 扣 webpack chunk + 补环境 + 固定时间戳参与项实验 | ✅ 11/11 通过 |
| [pro15](pro15_mihuashi_wasm/) | 米画师 WASM 签名 | Rust wasm-bindgen 64KB 模块 + 补环境 + 固定 nonce 确定性验证 | ✅ 11/11 通过 |
| [pro11](pro11_scrape_wasm_sign/) | scrape.center WASM 签名 | wasm2wat 反汇编直出公式（232B 教学案例） | ✅ 10/10 通过 |
| [pro25](pro25_hainan_td/) | 海航 TrustDecision blackBox | WASM 指纹 SDK：payload 解析 + 会话 key 恢复（field3 XOR 流）+ import 对象映射 | 🔒 5/5 通过 |
| [pro33](pro33_boss_zhipin_jsvmp/) | BOSS直聘 __zp_stoken__ | JSVMP 双层解释器 + 186 项环境指纹 + seed/ts 绑定与 UTF-8 变体编码 | ✅ 3/3 通过（线上 5/5） |
| [pro34](pro34_jd_main_h5st/) | 京东主站 h5st v5.3 | 35 解释器 VM + 10 段结构 + seg7 编解码（变体哈希链未还原） | 🔒 3/3 通过 |
| [pro35](pro35_jd_union_h5st/) | 京东联盟 h5st | 236KB stack VM + rev3/rev4 乱序 + seg8「加密实为编码」 | ✅ 3/3 通过（SDK 10/10 段） |
| [pro36](pro36_douyin_abogus/) | 抖音 a_bogus | SDK 字节码 VM + SM3 国密 + RC4 变体 + 双字母表 Base64 | ✅ 3/3 通过（对拍 16/16） |
| [pro37](pro37_xhs_mns_x3/) | 小红书 mns x3 | JSVMP + 自定义 XTEA + F6 静态置换 + 自定义字母表 | ✅ 4/4 通过（VM 10/10） |

### 环境指纹 / 补环境

| 编号 | 项目 | 技术点 | 状态 |
|------|------|--------|------|
| [pro24](pro24_chuanhang_constid/) | 川航 顶象 ConstID | `window.sss` 自定义字母表 base64 + json2 序列化 + 3 个 XOR 解码器 | ✅ 21/21 通过 |

### 字体反爬

| 编号 | 项目 | 技术点 | 状态 |
|------|------|--------|------|
| [pro30](pro30_dianping_font/) | 大众点评 字体反爬 | 动态 WOFF 字体 + PUA 码点混淆 → cmap/glyph 两级映射还原 | ⚠️ 7/7 通过（站点已改版） |

### 内容加密

| 编号 | 项目 | 技术点 | 状态 |
|------|------|--------|------|
| [pro19](pro19_qdjiangzhiyun/) | 起点小说 正文解密 | br 压缩 + execjs 执行 JS 解密（纯算还原） | ✅ 通过 |
| [pro31](pro31_tcl2024_jscontent/) | 天辰文学 JS 内容加密 | 章节响应体 = 可执行 JS 包装正文，判别器 + node 执行还原骨架 | ⚠️ 3/3 通过（站点已死亡，算法未还原） |

> 验证码类项目（极验/顶象/网易易盾等）与瑞数 WAF 专项不在本仓库收录范围内。

## 经典归档迁移

`经典 不开源/` 下 8 个实战项目已整理进本仓库：5 个新站点 + 3 个同站点升级。迁移范围为**纯算法复现、≥3 组样例与核心参考脚本**；完整工具链、全部 SDK 与抓包原始数据不迁移。

| 经典归档项目 | 去向 | 迁移内容 |
|------|------|---------|
| BOSS直聘-JSVMP逆向-2026-08-29 | [pro33](pro33_boss_zhipin_jsvmp/) | 双层 VM 纯算法 + 环境常量 + 线上验证脚本 |
| 京东主站-h5st签名-2026-08-30 | [pro34](pro34_jd_main_h5st/) | 段结构 + seg7 编解码 + 参考路线（哈希链未还原） |
| 京东联盟-h5st签名-2026-08-30 | [pro35](pro35_jd_union_h5st/) | 完整纯算法 + 同 run 逐段 diff 脚本 |
| 抖音-a_bogus签名-2026-08-30 | [pro36](pro36_douyin_abogus/) | 485 行纯函数引擎 + 对拍脚本 + 脱敏样例 |
| 小红书-mns签名-2026-08-31 | [pro37](pro37_xhs_mns_x3/) | 纯算法 + X-S/X-S-Common 组装参考 |
| 拼多多-anti_content逆向-2026-08-30 | [pro18](pro18_pinduoduo_anticontent/)（升级） | 纯算法替换补环境主线，原版引擎留作备份 |
| 今日头条-a_bogus签名-2026-09-02 | [pro28](pro28_toutiao_abogus/)（升级） | 148 字符纯算法替换旧版 Node 主线，SDK 留作备份 |
| 雪球网-md5__1038-WAF签名-2026-08-16 | [pro05](pro05_xueqiu_md5_1038/)（升级） | 补齐归档未完成的纯算实现 + 确定性对拍向量 |

## 技术分类

| 标签 | 含义 | 典型特征 |
|------|------|---------|
| `encrypt` | 参数加密 | MD5/SHA/AES/RSA/SM/自定义签名 |
| `obfuscate` | 混淆还原 | OB/sojson/控制流平坦化/字符串数组 |
| `debug` | 反调试 | debugger 检测/定时器/自校验 |
| `waf` | WAF 逆向 | 瑞数/加速乐/Cloudflare/Akamai |
| `wasm` | WASM 保护 | 导出函数、wasm2wat |
| `vm` | VM 保护 | JSVMP、字节码解释器 |
| `env` | 环境指纹/补环境 | Navigator/Canvas/WebGL 检测 |
| `font` | 字体反爬 | WOFF 动态字体、PUA 码点、cmap/glyph 映射 |

## 新增项目规范

- 目录：`pro{NN}_{站点关键词}/`，含 `README.md`（六段式文档）+ `main.py`（单文件复现）
- 复现标准：一条命令跑通、依赖最少、内置 ≥3 组实战抓包样例自证、不依赖网络、注明失效边界
- 新项目按 `_template/` 接入

## 第三方文件与版权

仓库内随项目附带以下第三方文件，版权归其原始权利人所有，仅以学习与研究目的归档（详见 [LICENSE](LICENSE) 附加条款）：

| 项目 | 第三方文件 | 权利方 | 性质 |
|------|-----------|--------|------|
| [pro05](pro05_xueqiu_md5_1038/) | `md1038_generator.js` | 雪球网 | 签名算法逐行移植（原 webpack 函数） |
| [pro12](pro12_kugou_login_crypto/) | `kugou_aes_module.js` / `rsa_ref.js` / `kg_aes_ref.js` | 酷狗音乐 | 登录加密模块原版 |
| [pro13](pro13_yinghua_jsjiami/) | `player.js` / `player_clean.js` / `strings.json` | 樱花动漫 | jsjiami v7 混淆原版及解混淆中间产物 |
| [pro15](pro15_mihuashi_wasm/) | `mhs_fe_sign_bg.wasm` | 米画师 | Rust wasm-bindgen 签名模块 |
| [pro16](pro16_gdtv_wasm/) | `vendor_w.js` | 荔枝网 | webpack 打包的 API 签名 SDK |
| [pro17](pro17_aiqicha_abclite/) | `abclite-2061-s.original.js` / 解码产物 / `scripts/` | 百度 | ABCLite SDK（dlswbr.baidu.com 动态拉取） |
| [pro18](pro18_pinduoduo_anticontent/) | `generator/` | 拼多多 | anti_content fbeZ 引擎原版 |
| [pro28](pro28_toutiao_abogus/) | `bdms_browser.js` / `sdk-glue.js` / `runtime_bundler_52.js` | 字节跳动（今日头条） | 签名 SDK webpack 原版（其余 js 为自研补环境脚本） |
| [pro36](pro36_douyin_abogus/) | `reference/sign_engine.js` | 字节跳动（抖音） | a_bogus 签名函数提取/移植版 |
| [pro30](pro30_dianping_font/) | 12 个 `*.woff` / `*.npy` | 大众点评（美团） | 2022 年字体反爬抓包存档 |
| [pro32](pro32_oatd_cloudflare/) | `stealth.min.js` | puppeteer-extra 项目（MIT） | 反检测插件提取版 |

说明：

- 以上文件如需商用或二次分发，请自行向权利方获取授权
- 未随仓库分发的第三方代码（pro24 顶象 ConstID、pro34/pro35 京东 `sign.js`、pro37 Node 补环境产物等）已在对应 README 注明获取方式
- 抓包样例（含 pro04 验证码图片、pro19 密文向量等）均为已过期或脱敏数据，仅作验证用例；经典归档迁移项目统一使用过期 token、占位值或固定随机源的确定性向量

## 致谢与说明

- 分析工具链：Babel AST 解混淆、wasm2wat / wasm-decompile、Chrome DevTools Protocol（js-reverse MCP）
- 各项目 `README.md` 均注明复现对象、样例来源日期与失效风险
