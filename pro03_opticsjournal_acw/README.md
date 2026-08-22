# 中国光学期刊网 — 阿里云 WAF `acw_sc__v2` cookie 生成

> 复现对象：`北大信研院/pro24 科技文献 中国光学期刊网/` · 技术分类：`waf` `debug` · 状态：✅ 可复现（4/4 通过）

## 站点与目标

- 站点：`https://www.opticsjournal.net/`（中国光学期刊网，2025-07 实测）
- 加密参数：cookie `acw_sc__v2`（由挑战页内嵌 `var arg1='...'` 计算而来）
- 目标接口：`/Search/Article` 搜索接口（POST，需 `__RequestVerificationToken`），文章正文页

## 技术要点

- 算法：**固定置换表 unsbox + 固定 key XOR**——`arg2 = hexXor(unsbox(arg1), "3000176000856006061501533003690027800375")`，完全静态无随机性（与贤集网同算法）
- 保护类型：阿里云 WAF acw 系列经典挑战（`acw_sc__v2`）；叠加反调试 + TLS 指纹 + 设备指纹
- 一句话概括：算法本身可 Python 直接掉包；真正的难点是**请求链**（curl_cffi 指纹 + 刷新 cookie 后 reload）

## 逆向摘要

- 入口定位：首访请求返回 405 或挑战页（`error.js`，OB 混淆 + 反调试），页面里 `var arg1='(.*?)'` 正则即可提取
- 还原过程：
  1. 反调试识别：`Function.prototype.constructor = function(){}`（禁 eval/Function 构造）+ `_0x355d23` 递归执行 `"debugger"` 字符串 + `window.__phantomas` 检测——补环境执行时需替换/绕过
  2. 解混淆后定位 `String.prototype.unsbox`（40 位置换表）与 `String.prototype.hexXor`（逐 2 hex 字符异或）两个原型方法，`arg2 = arg1.unsbox().hexXor(key)`，`setTimeout('reload(arg2)', 2)` 设 cookie 后跳转
  3. JS→Python：`unsbox` 直接按表索引取值（结果第 j 位 = 源第 `table[j]-1` 位）；`hexXor` 用 `f"{a^b:02x}"` 处理补零
- 附加发现：同样参数 requests 请求 405、curl_cffi（impersonate=chrome110）请求 200——**TLS 指纹层校验**；触发挑战后"小黑屋"约 10 分钟（疑似设备指纹，换浏览器无效）

## 复现

```bash
# 依赖：无（标准库）
python main.py
```

- 样例输入 → 期望输出（2 组实战 arg1 + 2 组逆变换自洽验证；期望值经原 JS 逻辑 node 交叉验证）：

| arg1 | 期望 arg2（acw_sc__v2） |
|------|------------------------|
| `A07B3202783CCB56A5C8E12165FA8D5ABC81F1CE` | `6881a1c187408f146a36c4d18ea6640b84faccb4` |
| `1BE274EA5756C559143C74D058B985C99B8B8961` | `68808e7975b97b4b5a506599679bdce23069bb1e` |

## 验证与实测

- 样例对比：4/4 通过（2 组正向 + 2 组 `unsbox_inv(hexXor(arg2, key)) == arg1` 往返自洽）
- 真实请求验证：2025-07 `spider_opticsjournal.py` 全站跑通（2008-2025 年文章按年分页，`acw_sc__v2` + `__RequestVerificationToken` 刷新流程：请求 → 检测挑战 → 计算 arg2 → 设 cookie 重试 → 200）

## 备注

- 失效风险：key `3000176000...` 与置换表如被服务端更新，需重新抓挑战页；405 挑战频发时是触发设备指纹，需等待约 10 分钟
- 坑：挑战页提取 `arg1` 用正则 `var arg1='(.*?)';` 注意**只匹配小写 var**（混淆代码里 `arg1` 是明文字符串）；`__RequestVerificationToken` 每页变化需从响应 HTML 的 `<input name="__RequestVerificationToken">` 刷新；下载 PDF 需要登录 cookie，未做
- 坑：`arg1` 全大写、`unsbox` 保留大小写、`hexXor` 的 `toString(16)` 输出**小写**——生成的 `acw_sc__v2` 一律小写；若做逆变换自洽验证需统一大小写再比较
