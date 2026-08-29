# 公安部统计上报编码链 + AST 反混淆教学

> 复现对象：`spider research/其他/pro16 公安部/` · 技术分类：`obfuscate` · 状态：✅ 可复现（编码链 5/5，AST demo 可运行）

## 站点与目标

- 站点：https://www.mps.gov.cn（公安部官网，TRS WCM 内容管理系统）
- 加密参数：无签名参数（搜索 API 为明文 form）——逆向对象是**统计上报编码链**与**AST 逆向教学方法**
- 目标接口：`POST https://app.mps.gov.cn/searchweb/searchPic`（站内搜索，明文参数 fullText/pageNow/pageSize 等）；统计上报为 1×1 像素 `access?<双层URL编码>` Image Beacon

## 技术要点

- 算法/保护类型：自定义 Base64（encode64，ASCII 与标准 base64 完全一致）+ 双层 encodeURIComponent 编码链
- 混淆情况：无（站点为 jQuery 明文 JS）——本项目的混淆内容在**教学演示**中（AST 反混淆 demo 自带字符串数组混淆样例）
- 一句话概括：统计上报参数经 `encode64 → 双层 URL 编码`（或 `JSON.stringify → 双层 URL 编码`）链处理后发送

## 逆向摘要

- 入口定位：直接读 search_gxb.js（明文 jQuery 脚本），搜索 `encodeURIComponent` 定位统计函数簇
- 还原过程：
  1. 提取原站 4 个函数：`encode64`（标准字符集自实现 Base64）、`t`（去 HTML 标签+URL编码）、`u`（Base64+双层URL编码）、`a`（JSON+双层URL编码）
  2. Node 直接 eval 原站函数跑样例 → 得到真实输出作为对照向量
  3. JS→Python 差异：`encodeURIComponent` 安全字符集为 `A-Za-z0-9 - _ . ! ~ * ' ( )`（`quote(safe="-_.!~*'()")`）；`JSON.stringify` 不转义非 ASCII（`json.dumps(ensure_ascii=False)`）；encode64 对中文产生 charCodeAt 截断垃圾（越界 charAt 返回 ""），该缺陷路径不复现
- 附带：ast_deobfuscate_demo.js（Babel AST 教学演示）+ AST教学指南.md（从零学 AST 逆向的完整文档）

## 复现

```bash
# 依赖: 仅标准库 (base64/json/re/urllib)
python main.py

# AST 教学 demo (需 node + npm i @babel/parser @babel/traverse @babel/generator)
node ast_deobfuscate_demo.js
```

- 样例输入 → 期望输出（内置在 `main.py` 的 `SAMPLE_CASES`，5 组，取自原站 search_gxb.js 函数实测 2026-06）：

| 函数 | 输入 | 期望输出 |
|------|------|---------|
| encode64 | `hello world` | `aGVsbG8gd29ybGQ=` |
| encode64 | `abc` | `YWJj` |
| t | `<p>公安部</p>通知` | `%E5%85%AC%E5%AE%89%E9%83%A8%E9%80%9A%E7%9F%A5` |
| u | `test/123` | `dGVzdC8xMjM%253D` |
| a | `{name:公安部, id:123, list:[1,2]}` | `%257B%2522name%2522…%257D`（双层 URL 编码 JSON） |

## 验证与实测

- 样例对比：5/5 全部通过（期望值由原站 JS 函数在 Node 中实测生成）
- 真实请求验证：2026-06 原项目 spider 实测搜索接口可用（README 记录响应结构）；统计 Beacon 为 1×1 图片不可见，未单独验证

## 备注

- 失效风险：站点 CMS 升级可能移除统计脚本；编码函数是站点自研的通用片段，本身无时效性
- 坑：encode64 仅对 ASCII 与 `base64.b64encode` 一致——中文输入时 JS charCodeAt 的 16 位截断 + 越界 charAt 会产生垃圾输出，Python 复现时应明确边界不模拟缺陷路径
- 教学定位：本项目主要价值在 AST 逆向教学（指南 + demo），编码链为附带产物
