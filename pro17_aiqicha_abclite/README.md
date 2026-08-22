# 爱企查 — ABCLite-2061 SDK 双重转义字符串还原 + 反调试/设备指纹检测

> 复现对象：`spider research/其他/pro26 爱企查 反调试/` · 技术分类：`debug` + `env` · 状态：✅ 可复现（42/42 通过，2026-08-19 验证）

## 站点与目标

- 站点：`https://aiqicha.baidu.com/`（百度爱企查，原项目 2026-06-30 CloakBrowser 分析）
- 加密对象：`https://dlswbr.baidu.com/heicha/mw/abclite-2061-s.original.js`（206KB，百度自研 ABCLite SDK，加载器 `abclite-2061-s.js` 每 20 分钟刷新拉取）
- 目标产物：字符串解码链还原 + 7 类检测判定逻辑（DevTools/WebDriver/无头/指纹/toString 篡改）；第 2 层 ACS-2061 仅结构（AES 密钥未提取）

## 技术要点

- 算法：**`\xHH` 双重转义字符串混淆**——CDN 原始文件是 `'\\x6f\\x75...'`（双反斜杠，JS 字符串字面量解析后得到文本 `\xHH`，运行期再二次解析）；分析会话归一化后用 `\xHH`→字符 解码
- 保护类型：eval getter 劫持 + `Error().stack` 找 `evaluate@debugger` 标记（比按键拦截高级）；WebDriver 全局标记；无头窗口尺寸；WebGL/Canvas/Battery 指纹
- 一句话概括：反调试核心是**栈分析**而非按键拦截——DevTools 打开时 Chrome 会在 eval 堆栈注入 `evaluate@debugger` 行；字符串混淆靠 JS 引擎原生转义，爬虫无需理会

## 逆向摘要

- 入口定位：`abclite-2061-s.js` 加载器 → 动态拉取 original SDK（`?_=<parseInt(u/1728e5)>` 缓存破坏）→ `decode_script.py` 解码 → 反调试代码全明文
- 还原过程：
  1. 解码链：`raw(双反斜杠) → 归一化(单反斜杠) → decode_hex → 明文`；`decode_hex(formatted)+'\n' == abclite_decoded.js` **逐字节复现**（9753 个转义串）
  2. DevTools 检测：劫持 `window.eval` getter → 每次 eval 抓 `Error().stack` → 命中 `evaluate@debugger` 且下一行 `@debugger` 开头即判定
  3. 无头检测：固定分辨率 800×600×1200 → flag 5000；`outerWidth==0` → 5001（常量 0x320/0x258/0x4b0 已在解码代码验证）
  4. WebDriver：6 个全局标记（`__driver_evaluate`/`__nightmare` 等）遍历收集；浏览器特征 chrome.runtime→7100、webdriver+selenium 双 string→7200、WebGL→600/601
  5. toString 篡改：原生调用抛异常时堆栈行数变少 → flag 100
- JS→Python 差异：`\xHH` 在 Python 普通字符串里会被当转义吃掉，必须用 `r"\x65..."` 原始串；JS 字符串字面量对 `\\x` 先解析一次（双反斜杠→单反斜杠）

## 复现

```bash
# 依赖: Python 标准库 (0 第三方, 无需 node/网络)
python main.py   # 42 项: 编码链/加载器/检测判定/ACS 结构
```

| 验证项 | 结果 |
|--------|------|
| 编码链 ×11（9753 转义计数 / 双反斜杠形式 / 解码管道逐字节 / 端到端 CDN→明文 / 样例 ×5） | ✅ |
| 加载器 ×3（版本 2061 / 20 分钟缓存破坏 / BCat_2061 七方法） | ✅ |
| 检测逻辑代码在解码产物中实存 ×3（栈链/尺寸常量/驱动标记+flag 码） | ✅ |
| DevTools 判定 ×3 / WebDriver ×3 / 窗口尺寸 ×3 / 浏览器特征 ×4 / toString ×3 | ✅ |
| ACS-2061 结构 ×9（字段表 12 键 / 签名格式 / extraTooLong / 版本） | ✅ |

## 验证与实测

- 样例对比：42/42 通过；`decode_hex(formatted) + '\n'` 与 `abclite_decoded.js` 逐字节一致；`decode(unescape(raw))` 含全部明文检测标记（2026-08-19）
- 真实请求验证：原项目 2026-06-30 实测——**搜索需强制登录**（扫码/微博/微信/QQ），未登录跳转 `login?u=`；建议 Hook `BCat_2061` 返回假数据 + 有效登录 Cookie 维持会话

## 备注

- 失效风险：SDK 版本号（2061）与加载 URL 随发版变化；**每 20 分钟刷新**导致两次抓包内容不同（raw 与 formatted 是两次捕获，检测逻辑一致）；ACS AES 密钥混淆在代码中未提取（报告标注后续方向）
- 绕过：CDP 直连可避 WebDriver 检测；窗口尺寸设常规值；`evaluate@debugger` 检测需在页面加载前 patch eval getter（本仓库 `pro05` 的补环境路线可参考）
