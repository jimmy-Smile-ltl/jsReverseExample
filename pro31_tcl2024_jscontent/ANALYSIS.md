# ANALYSIS — 天辰文学 (tcl2024.com) JS 内容加密 机制分析

> 分析日期：2024-06（原 notebook）→ 2026-08-22（站点死亡复测）
> 状态：站点已死亡，密文样例缺失，解码算法未还原

## 1. 站点与数据流

```
目录页 https://www.tcl2024.com/book/{book_id}
  └─ dds[].a["href"]  →  章节页 https://www.tcl2024.com/files/article/html555/0/768/{id}.html
                          └─ 响应体不是 HTML 正文, 而是 JS 代码 (密文)
                               └─ js2py.eval_js(txt) → 真实正文
```

- 书 id=768（html555/0/768 目录层级），章节 id 连续递增（647137、647139…）
- 章节响应体整体就是 JS：原文 notebook 中 `txt = txtRes.text` 后直接 `eval_js(txt)`

## 2. 原 notebook 流程（逐 cell 还原）

| 步骤 | 代码 | 说明 |
|------|------|------|
| 目录解析 | `BS(pageRes.text)` + `dds[].a["href"]` | 章节链接列表 |
| 请求章节 | `requests.get(txtUrl, headers=headers)` | 带 UA + 百度统计 Cookie（Hm_lvt/Hm_lpvt） |
| 执行还原 | `trueText = js2py.eval_js(txt)` | **核心**：响应体当 JS 执行 |
| 清洗 | `re.sub("&nbsp;","",trueText).replace("<br>","\n")` | HTML 实体/换行规整 |
| 落盘 | `file.write(...)` | 追加到 山沟皇帝.txt |

## 3. 机制本质：响应式 JS 包装

- 服务端把正文编码进一段可执行 JS（浏览器 `script` 标签天然执行渲染，requests 拿到的是包装代码）
- 常见包装形态（未确认此站用哪种，站点已死）：
  1. `document.write("<p>正文…</p>")` — 正文直接内嵌
  2. `var a="…"; document.write(unescape(a))` — 编码 + 内置解码函数
  3. 字符串拼接/位移/XOR 后 write — 有明确可还原算法
- 形态 1 无需「算法还原」，eval 即得；形态 2/3 才有纯算还原价值 —— 取决于真实密文

## 4. 复现环境变更（js2py → node）

原 notebook 在 anaconda Python 3.11 + js2py 下运行。当前环境：

- anaconda 已损坏（Lib 目录缺失），改用 Python 3.12
- js2py 与 Python 3.11+ 不兼容：`injector.append_arguments` 中 `six.get_function_code`
  依赖已移除的 code object 属性 → `KeyError: 3`；js2py 已停维护无修复
- 本仓库用 `eval_chapter.js`（node + 最小 DOM stub）完成同一「执行还原」语义

## 5. 缺失材料清单（要完成算法还原需要）

1. **一份章节 JS 密文**（几十 KB 的 txtRes.text 原文）—— 站点死亡后唯一来源是
   当时运行环境的历史缓存/抓包文件，notebook outputs 未保存
2. 站点复活（或找到同程序镜像站：天辰文学系列小说站共用一套程序，
   编码函数通常相同）
3. 拿到密文后的还原路径：
   - 若为 `document.write` 内嵌 → 直接 eval（本仓库骨架已支持）
   - 若含解码函数 → AST/正则提取解码逻辑 → Python 复现 → 填充 SAMPLE_CASES

## 6. 与仓库其他项目的关联

| 项目 | 站点 | 形态 | 状态 |
|------|------|------|------|
| pro19_qdjiangzhiyun | 起点读书 | br 压缩 + execjs JS 解密 | ✅ 已纯算还原 |
| pro31_tcl2024_jscontent | 天辰文学 | 响应体 = JS 包装正文 | ⚠️ 执行式还原骨架 |
