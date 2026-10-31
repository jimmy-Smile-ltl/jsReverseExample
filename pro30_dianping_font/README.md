# 大众点评字体反爬 — PUA 码点 → glyph → 真实字符还原

> 复现对象：`无限集数/电商社交/大众点评/` · 技术分类：`font` `encrypt` · 状态：⚠️ 接口失效（2022-03 抓包存档，站点已改版）

## 站点与目标

- 站点：https://www.dianping.com（大众点评店铺页，2022 年版本）
- 加密参数：页面文字本身 —— 数字与常用汉字用自定义 WOFF 字体渲染，真实字符字形被随机映射到 Unicode PUA 私有区码点（U+E000~U+F8FF），直接抓 HTML 得到乱码
- 目标接口：店铺详情页 HTML + CSS 中的 `@font-face` 字体 URL（当次会话动态下发）

## 技术要点

- 算法/保护类型：字体反爬（font anti-crawling）——动态 WOFF 字体 + 字形码点混淆
- 混淆情况：无 JS 混淆；防护在字体层（cmap 映射随机化）
- 一句话概括：`页面码点 → cmap 查 glyph 名 → 离线映射表查真实字符` 三段还原

## 逆向摘要

- 入口定位：页面文字乱码 → 检查 CSS 发现 `@font-face` 动态字体 → 下载 .woff 分析
- 还原过程：
  1. fontTools 解析 woff：cmap 表给出「码点 → glyph 名」（glyph 命名规则 `uniXXXX`，如 `unie8cd` = U+E8CD）
  2. 字形比对（视觉/OCR）建立「glyph 名 → 真实字符」映射表，以 .npy（pickle dict，603 项 = 数字 0-9 + 600 常用汉字）存档
  3. 还原时逐码点查两级映射；本复现覆盖 2/3 两步（离线），第 1 步字体抓取依赖站点（已失效）
- 关键差异：**每字段独立字体** —— 6 组字体（address/address-num/hours/review-shopdesc-dishname/reviewTag/shopNum-tagName），同一字符在不同字体中码点不同（'1' 在 address 中是 `0xe8cd`，在 address-num 中是 `0xf271`），映射表必须按当次会话抓取

## 复现

```bash
# 依赖 (2 个第三方)
pip install numpy fonttools

# 运行 (一条命令, 输出即验证)
python main.py
```

- 样例输入 → 期望输出（内置在 `main.py` 的 `SAMPLE_CASES`，7 组，取自 2022-03 抓包字体存档）：

| 字体 | 码点序列（页面密文） | 期望明文 |
|------|------|---------|
| address | `0xe8cd 0xe1b9 0xf3db … 0xe37f`（10 个） | `1234567890` |
| address-num | `0xf271 0xf413 0xefd0 0xeb59 0xf701` | `12345` |
| hours | `0xf763 0xf27b 0xecd0 0xf1a3 0xea49` | `12345` |
| review-shopdesc-dishname | `0xed08 0xf525 0xefaa 0xf1ec 0xf7b2` | `12345` |
| reviewTag | `0xe6f9 0xe355 0xf4dd 0xf5c7 0xef74` | `12345` |
| shopNum-tagName | `0xe397 0xf79a 0xf778 0xf7f8 0xf760` | `12345` |
| address（汉字） | `0xe49c 0xeabc 0xf76c 0xe95d 0xea3a` | `店中美家馆` |

## 验证与实测

- 样例对比：7/7 全部通过（6 组数字 + 1 组汉字，跨 6 个字体文件）
- 真实请求验证：2022-03 抓包时完整跑通（原项目 spider.ipynb + dianping.csv）；此后站点改版，字体方案变更，**未重测且已知失效**

## 备注

- 失效风险：**站点已改版**（2022 后大众点评前端多次重构），本复现价值为字体反爬类型的方法论存档与离线验证
- 坑：woff 用 fontTools 加载时 `post.stringData` 有 2 字节冗余（提示可忽略）；npy 为 0-d object array（`np.load(allow_pickle=True).item()` 取 dict），其中含 `.notdef`/`x` 等非字符项需过滤
- 目录内 12 个 woff/npy 文件为 2022 年大众点评字体抓包存档，版权归其原始权利人，仅作学习研究归档
