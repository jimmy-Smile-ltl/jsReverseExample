# 樱花动漫 — jsjiami.com.v7 字符串表解混淆（自定义 base64 + RC4）+ 5 层反调试

> 复现对象：`spider research/其他/pro20 樱花动漫视频 解混淆 反调试/` · 技术分类：`obfuscate` + `debug` · 状态：✅ 可复现（29/29 通过，2026-08-19 验证）

## 站点与目标

- 站点：`https://www.yh5dm.net/`（樱花动漫，原项目 2026-06-30 分析）
- 加密对象：`https://svip.yinghuaz.cc/assets/player.js`（110KB，jsjiami.com.v7 + Parcel 打包）；另有页面内联反调试脚本（1676B）
- 目标产物：`player_clean.js`（全部字符串引用还原为明文）；`apiToken`/`api/resolve.php` 链路说明视频地址需服务端 token

## 技术要点

- 算法：**自定义 base64（小写字母表在前！）+ RC4 流密码**；字符串表 1121 条，解码偏移 `index - 0x112`
- 保护类型：jsjiami.com.v7 字符串加密 + 别名链（`_0x2b2717 = _0x12d4`）+ while-switch 控制流混淆 + 5 层纯前端反调试（F12/快捷键/右键/窗口尺寸 debugger/Vue 通知）
- 一句话概括：字符串全部走 `_0x12d4(index, key)` 解密——**字母表是小写开头**（标准 base64 大写开头），混用必炸；反调试是入门级属性覆盖即可绕过

## 逆向摘要

- 入口定位：`player.js` 头部 `var _0xodD='jsjiami.com.v7'` 标记 → 解码器 `_0x12d4` 定义处（3627 行）→ `_0x1a56()` 字符串表 → 提取 1121 条为 `strings.json`
- 还原过程：
  1. 解码链：`index -= 0x112` → 取表 → **自定义 base64 解码**（`abcdefghijklmnopqrstuvwxyz` 开头）→ 字节按 UTF-8 还原 → 标准 RC4（KSA + PRGA）逐字符 XOR
  2. JS→Python 差异：base64 压缩循环用 `(-2*i)&6` 位移取 0/2/4/6；`decodeURIComponent` 等价 `bytes.decode('utf-8')`；RC4 输入是字符而非字节（`charCodeAt`/`fromCharCode`）
  3. 全量验证：正则扫出 1157 处合法引用（51 个不同 key），全部解码成功；1135 处明文出现在 `player_clean.js` 基准中（22 处缺失为 switch 调度器的 `parseInt` 数字值）
  4. 反调试：`onkeydown` 拦截 F12(123)/Ctrl+Shift+I(73)/Ctrl+U(85)/Ctrl+S(83) + `oncontextmenu` + `setInterval` 轮询 `outerWidth-innerWidth > 160` 触发 debugger
  5. 绕过：`document.onkeydown = null` 直接恢复（未用 defineProperty 保护）；DevTools 独立窗口模式免于尺寸检测；爬虫用 curl_cffi 完全不受影响

## 复现

```bash
# 依赖: Python 标准库 (0 第三方, 无需 node/网络)
python main.py   # 29 项: 解码器样例/全量扫描/基准交叉/反调试判定
```

| 验证项 | 结果 |
|--------|------|
| 解码期望值 ×11（含 3 条中文 UTF-8，与解混淆报告+player_clean.js 一致） | ✅ |
| 全量调用点扫描 1157 处 0 失败 ×1 / 与 player_clean.js 交叉 1135/1157 ×1 | ✅ |
| 自定义字母表必要性证明（标准 base64 解码失败）×1 | ✅ |
| 表结构/标记/别名链/基准文件 ×4 | ✅ |
| 反调试按键拦截判定 ×7 / DevTools 尺寸检测判定 ×4 | ✅ |

## 验证与实测

- 样例对比：29/29 通过；解码值（`apiToken`、`.m3u8`、`无法解析视频。` 等）与 `player_clean.js` 明文逐字一致
- 真实请求验证：原项目 2026-06-30 用 curl_cffi 实测播放页/接口均不受反调试影响；token 由服务端生成（AES 密钥在服务端，客户端无法自主生成）

## 备注

- 失效风险：字符串表随前端发版更换；`strings.json` 需从新版 `player.js` 的 `_0x1a56()` 重新提取；反调试为页面 inline script，与 player.js 独立更新
- 坑：字母表小写在前；解码偏移 0x112 是 jsjiami v7 固定值；`'='` 在字母表第 64 位（被处理为值 64）；表条目无 `=` 填充；`player_clean.js` 按字节比源文件更大（明文膨胀+UTF-8 多字节），应比字符数
