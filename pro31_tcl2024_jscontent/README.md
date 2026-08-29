# 天辰文学 (tcl2024.com) JS 内容加密 — 章节响应判别与还原骨架

> 复现对象：`无限集数/小说/山沟皇帝_tcl2024.ipynb` · 技术分类：`encrypt`（JS 内容加密）· 状态：⚠️ 接口失效（站点已死亡，真实密文样例不可获取，算法未还原）

## 站点与目标

- 站点：https://www.tcl2024.com（天辰文学，盗版小说站，2024-06 抓取时可用）
- 加密参数：**章节正文本身** —— 章节 URL 返回的不是 HTML，而是可执行 JS 代码，执行后才产生正文
- 目标接口：`GET https://www.tcl2024.com/files/article/html555/0/768/{章节id}.html`（响应体为 JS 密文）

## 技术要点

- 算法/保护类型：JS 内容加密（响应式 JS 混淆）——服务端把正文编码进一段 JS（形如 `document.write(...)` 或字符串拼接），爬虫拿到的是代码而非文字
- 混淆情况：密文 JS 的编码函数未还原（样例缺失）；原项目用「执行还原」绕过（js2py.eval_js），不解析算法
- 一句话概括：`GET 章节 → 响应是 JS → eval 执行 → 正文`，执行式还原而非算法还原

## 逆向摘要

- 入口定位：requests 抓章节发现响应是 JS 代码（页面源码 `#txt` 容器里嵌着 script）→ notebook 直接对响应体 `js2py.eval_js(txt)` 得正文
- 还原过程：
  1. 原项目（2024-06）流程：`requests.get(txtUrl)` → `trueText = js2py.eval_js(txt)` → `&nbsp;` 清洗 + `<br>` 换行 → 存 txt
  2. 机制本质：服务端用 JS 包装正文（执行才出字），客户端浏览器天然可渲染，requests 拿到的是包装代码
  3. js2py 与 Python 3.12 不兼容（injector 依赖旧版 code object 属性）→ 本复现改用 node 执行器（`eval_chapter.js`，stub 最小 DOM）
  4. **算法还原未完成**：站点死亡后无法获取真实密文样例，解码函数（编码方式未知）无法还原；本复现交付「判别器 + 执行还原骨架」并如实标注
- 关键差异：此站与 pro19（起点）同为小说站 JS 内容加密，但起点密文样例完整已纯算还原（br 解压 + JS 解密），此站缺样例只能执行式还原

## 复现

```bash
# 依赖: node (v16+); Python 仅标准库
python main.py
```

- 样例输入 → 期望输出（内置 3 组**机制演示用例**，自造 JS 密文形态 —— 真实密文随站点死亡不可获取，请勿引用为抓包样例）：

| 输入（响应形态） | 判别 | 期望还原 |
|------|------|---------|
| `document.write("第1章…<br>皇恩浩荡。")` | js_cipher | `第1章 山沟皇帝\n\n皇恩浩荡。` |
| `var a="第一回";…document.write(a+b…)` | js_cipher | `第一回 山沟\n\n完` |
| `<html><div id="txt">第1章 正文内容</div>` | html_plain | 原样放行不执行 |

## 验证与实测

- 样例对比：3/3 全部通过（判别器 + node 执行还原流程均可离线运行）
- 真实请求验证：2024-06 原 notebook 实测跑通（js2py 执行还原产出完整小说 txt）；**2026-08-22 复测站点已死亡**（DNS 解析存在但 CDN 节点 23.224.4.115 无响应，镜像域名 tcl2024.net/.cc/.org 全挂）

## 备注

- 失效风险：**站点已死亡**。本项目的价值在于记录「JS 内容加密」这一小说站反爬形态与执行式还原方法论；如站点复活或获得密文样例，可补齐 SAMPLE_CASES 并还原解码算法
- 坑：js2py 已停止维护、不兼容 Python 3.11+（`KeyError: 3` in injector），新环境用 node 执行器替代；node 输出 UTF-8 需在 subprocess 显式 `encoding="utf-8"`
- 详细机制分析见同目录 [ANALYSIS.md](ANALYSIS.md)
