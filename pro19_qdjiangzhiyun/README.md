# qdjiangzhiyun 小说站 — 章节正文解码: Base64 + 单字符插入扰动

> 复现对象：`无限集数/小说/qdjiangzhiyun_开局穿越杨宇霆，辅佐少帅抗日.ipynb` + `qdjiangzhiyun.js` · 技术分类：`encrypt` · 状态：✅ 可复现（9/9 通过，2026-08-20 验证）

## 站点与目标

- 站点：小说下载站 `qdjiangzhiyun.com`（章节页内嵌 JS 输出章节全文；页尾广告指向 bqg78.com）
- 目标：章节页 HTML（GET），正文藏在内嵌 JS 的 `var rid = parseInt("..."); var rcontent = "...";` 中，属**内容层防提取**而非 HTTP 参数加密
- 原项目：notebook 以正则提取 rid/rcontent 后 execjs 调 `decode_content`，实爬 506 章（2024-10-28，txt 3.5MB）

## 技术要点

- 算法：标准 Base64（`ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=` 默认表）+ **随机 1 字符插入扰动**
- 混淆情况：无 JS 混淆，但 rcontent 被压成单行 9KB 大字符串 + 章节页 JS 函数名经 `\x` 十六进制转义（`decode_content`、`_keyStr` 等）
- 一句话概括：**正文 = b64decode(rcontent 去掉下标 rid 处的 1 个垃圾字符)**，插入扰动专坑正则直接提取

## 逆向摘要

- 入口定位：notebook 抓包看到章节页 HTML 内嵌 `var rid/rcontent`，rid 逐章不同（4522/8384/7567…），怀疑 Base64——直接解发现错位乱码，去掉 rid 字符后还原
- 还原过程：
  1. 逆推：rcontent 字符集 = 标准 base64 表 + 冗余字符 → 单字符插入（不是编码变体）
  2. 解码链：`splice(rid) → base64.b64decode → utf-8`；`<br />` 段落标签在 pandas 阶段转 `\n`
  3. 交叉验证：原版 JS 经 node 实跑输出与 Python 实现 sha256 逐字节一致（2026-08-20 复验）
- JS→Python 差异：`substr(0,rid)+""+substr(rid+1)` 等价 `rcontent[:rid]+rcontent[rid+1:]`（无转义/编码差异，纯字节操作）

## 复现

```bash
# 依赖: Python 标准库 (0 第三方)
python main.py   # 解码器验证 + 2 组实战样例 + 敏感性/roundtrip (纯 Python, 无网络)
```

| 输入 | 期望输出 |
|------|---------|
| rid=4522, rcontent 9025 字符 | 2577 字符明文, sha256 `9d8ed5a6d7ef...1b40`, 首部"脑子寄存处，平行空间，少帅衍生小说" |
| rid=8384, rcontent 9525 字符 | 2667 字符明文, sha256 `5110cc5ae0b2...2b86`, 首部"张北县城外，军营如群星般林立" |
| encode(样例1明文) → decode | 还原 == 原文（roundtrip） |
| 不删垃圾字符 / 删错位置 | base64 解码错位或 UTF-8 非法（位置敏感证明） |

## 验证与实测

- 样例对比：9/9 全部通过（2026-08-20）；期望值经原版 JS node 实跑交叉验证一致
- 真实请求：原项目 2024-10-28 实爬 506 章全部成功（txt 3,552,295B）；本仓库未做网络复测（站点可用性未确认，接口未变不排除站点下线）
- 样本数据源：samples.json 含 2 组完整章节（rid/rcontent/期望 sha256），取自原项目 JS 文件

## 备注

- 失效风险：站点若改编码方案（如插 2 字符、换表）需重新抓包；`<br />` 是页面形态非解码必要步骤
- 坑：notebook 中 rcontent 为运行时提取、未持久化，第三组样例（rid=7567）无法从 notebook 复现——样例以 JS 文件内嵌的 2 组完整章节为准
