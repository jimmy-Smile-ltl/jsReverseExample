# 雪球网 — md5__1038 WAF 签名参数加密

> 复现对象：`spider research/财经/pro1 雪球网/` · 技术分类：`encrypt` `waf` · 状态：✅ 可复现（10/10 通过，2026-08）

## 站点与目标

- 站点：`https://xueqiu.com/`（雪球网，2026-08 实测，签名算法 2026-08-16 更新为当前版本）
- 加密参数：请求 URL 查询参数 `md5__1038`，格式 `<salt>-<LZW压缩编码>`（salt = `222029ad07`）
- 目标接口：全部 API（如 `/statuses/fundx/public/list.json`），缺签名被 WAF 302 跳认证页

## 技术要点

- 算法：SHA1 截取 `[10:26]` → 随机 0x2X 异或 → 环境 bit 打包 → **自定义 LZW 压缩 + 6-bit 字符表编码**
- 保护类型：WAF 签名；同 SDK 已迭代 3 代（salt 与字符表各不相同），当前为 65 字符自定义表
- 一句话概括：签名 = 标准哈希 + 随机扰动 + 自实现 LZW，四种技术路线均可产签名，见下

## 技术路线对比（本项目核心）

| 路线 | 实现位置 | 效果 | 说明 |
|------|---------|------|------|
| 1-RPC | 原项目 `1-RPC方案/`（Playwright+WebSocket） | 100% | 浏览器直算，最稳但重 |
| 2-纯算（旧版） | 原项目 `2-纯算方案/md5_1038_codec.py` | ~80% | 标准 base64+29 偏移，仅旧版 |
| 3-补环境 | 原项目 `3-补环境方案/`（vm_deobfuscated） | ~85% | 受 Web Crypto 限制 |
| **Python 直算** | **本仓库 `main.py`** | ✅ 10/10 | 新版全算法还原 + 手写 LZW 解码器 |
| **Node 直算** | **本仓库 `md1038_generator.js`** | ✅ | 原 webpack 函数逐行移植 |

## 逆向摘要

- 入口定位：页面 renderData 提取 `_waf_bd8ce2ce37`（wafToken）→ XHR 断点定位 `a4()` → webpack bundle 还原 `md5_1038(wafToken, url, serverTs)`
- 还原过程：
  1. `mp = encodeURIComponent(wafToken + method + salt + api)`（**全字符编码**，`=`→`%3D`、`/`→`%2F`）
  2. `m2 = SHA1[10:26]`；`m4` 每 2 hex 与随机 `0x20-0x2F` 字节异或；`F()` 环境 bit（Fisher-Yates 打包）
  3. `mc7 = XR(random|ms) + "a" + hex(ms)`；`mc = mc1|mc2|mc3|mc4|wafToken|serverTs|mc7`
  4. LZW 压缩（9bit 起始，每 512 码字 +1bit，KwKwK 分支）→ 6-bit 打包 → `salt + "-" + 编码`
  5. 原 JS 无 LZW 解码器，按编码器语义手写镜像（本仓库新增，用于解析任意 token 还原 mc）
- 三代演进：6 月版 salt `214d4f07715-` + 标准 base64+29 偏移表；6-24 中版补 sendBody；8-16 新版 salt `222029ad07` + 65 字符表（本仓库复现对象）

## 复现

```bash
# 依赖：Python 标准库（无第三方）；--node 交叉验证需本机 node
python main.py            # 10 项样例验证
python main.py --node     # 追加 Node 生成 → Python 解码结构比对
```

| 验证项 | 结果 |
|--------|------|
| m2 确定性 ×3（真实 wafToken/api，期望值与 Node 逐值一致） | ✅ |
| LZW roundtrip ×3（含 KwKwK 分支） | ✅ |
| 完整 token 结构 ×2（前缀 / wafToken / serverTs 回显 / mc4 时间） | ✅ |
| 随机性 ×1（相同输入两次输出不同） | ✅ |
| Node 交叉 ×1（md1038_generator.js 生成 → Python 解码还原 mc） | ✅ |

## 验证与实测

- 样例对比：10/10 通过；真实抓包 token（2026-08）长 196/206，本实现 197/202，同量级
- 真实请求验证：原项目补环境方案 2026-08-16 实测服务器接受签名（跳转认证 200 + API 200）；RPC 方案 100% 有效

## 备注

- 失效风险：salt/字符表随 SDK 更新变化（8 月已换代一次）；wafToken 从页面提取，有会话时效
- 坑：**Python `urllib.parse.quote` 默认不编码 `/`，与 JS `encodeURIComponent` 不一致，必须 `safe=''`**——否则 api 含 `/` 时签名被拒（原纯算 80% 通过率的部分根因）；LZW 字符表实际 65 字符（含 `=`），非字符表字符映射为 `65+charcode`
