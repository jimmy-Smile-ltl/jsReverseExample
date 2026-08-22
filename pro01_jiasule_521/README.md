# 加速乐 WAF 521 挑战 — `__jsl_clearance_s` cookie 生成

> 复现对象：`多探科技/pro20_cicc_report/`（分析文档 `pro20 加速乐 cdn 分析.md`） · 技术分类：`waf` · 状态：✅ 可复现（3/3 样例通过）

## 站点与目标

- 站点：锦天城律所 `https://www.allbrightlaw.com/CN/08.aspx`、中金公司 `https://www.cicc.com/business/list_214_223_1.html`（2026-05 实测，当前可能仍有 521 挑战）
- 加密参数：`__jsl_clearance_s`（挑战成功后随 `__jsluid_s` 一起携带）
- 目标接口：任意被保护页面，第一次直接 GET 返回 521

## 技术要点

- 算法：挑战页内嵌 `go({bts, chars, ct, ha, ...})` 数据；cookie = `bts[0] + chars 中两字符 + bts[1]`，暴力双循环枚举，使 `hash(cookie) == ct`
- 混淆情况：挑战页 JS 为字符串数组 + `_0x` 变量 OB 混淆（`code.js`/`main.js`），但**不需要还原**
- 一句话概括：`ha` 字段指定的是**标准 hash**（md5/sha1/sha256/sha512），hashlib 直接掉包；两字符暴力枚举最多 `22² = 484` 次，毫秒级出结果

## 逆向摘要

- 入口定位：Hook `document.cookie` setter（`Document.prototype.cookie` 描述符劫持）→ 拿到设置 `__jsl_clearance_s` 的混淆代码 → 控制台逐个 `console.log` 解密字符串函数 `_0x1ad9(...)`，还原出 `tn + '=' + 值 + '; path=/'` 的拼接结构
- 还原过程：
  1. 从混淆代码中确认核心是两段双重循环：外层取 `chars[i]`，内层取 `chars[j]`，拼接后喂 hash 函数
  2. 发现 hash 函数每次抓包"变来变去"（sha1/sha256 交替），实测与标准 hash 完全一致 → 掉包 hashlib，按 `ha` 字段动态选择
  3. 挑战成功后 `location.href` 跳回原页 → 带两个 cookie 第三次请求即 200

## 复现

```bash
# 依赖：无（标准库 hashlib）
python main.py
```

- 样例输入 → 期望输出（3 组全部来自实战抓包，2026-05）：

| ha | bts[0] | chars | 插入字符 | 期望 cookie |
|----|--------|-------|---------|------------|
| sha256 | `1778049662.41\|0\|jZmQ` | `FUYEtXpkETqffVXxELhYQJ` | `XY` | `1778049662.41\|0\|jZmQXYpjUP9gw%2FVC9du8Q0vSe84%3D` |
| sha1 | `1778039625.531\|0\|FXI` | `LvJjCOuSmCFzwFwIQaHMzg` | `mF` | `1778039625.531\|0\|FXImFluHCgKB6%2F7eCFKtQF6A1kU%3D` |
| sha256 | `1778053277.075\|0\|bpB` | `FUeMem8OxgYX6qGHbVcnPk` | `86` | `1778053277.075\|0\|bpB8642TpNqT2sPYF1%2FC9rYiDsg%3D` |

## 验证与实测

- 样例对比：3/3 通过（双重校验：cookie 值一致 + hash 自洽）
- 真实请求验证：2026-05 中金公司研报列表爬虫（`spider.py`）实跑成功——三步请求链：无 cookie → 521 挑战页 → 解出 cookie 重试 → 200；PDF 下载同样需要该 cookie

## 备注

- 失效风险：`go(...)` 数据每次抓包随机；chars 长度、hash 算法会变，但结构稳定
- 坑：`bts[1]` 是 URL 编码串（`%2F`），**直接拼接 hash，不要 decode**；`is: true` 时 cookie 拼接最后附加 `; path=/` 等属性，但值本身不受影响；`wt` 字段（1500ms 等待）是页面计时，抓包流程无需等待
