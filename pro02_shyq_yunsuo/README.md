# 社会舆情网 — 云锁 YunSuo WAF 挑战（security_session_verify）

> 复现对象：`北大信研院/pro27 舆情民生 社会舆情网/` · 技术分类：`waf` · 状态：✅ 可复现（4/4 通过）

## 站点与目标

- 站点：`http://shyq.org.cn/`（社会舆情网，2025-08 实测）
- 加密参数：URL 参数 `security_verify_data`；cookie `srcurl`（挑战后还需 `security_session_verify` + `security_session_mid_verify`）
- 目标接口：任意页面，首次 GET 返回 JS 挑战页（即 404-1.html）

## 技术要点

- 算法：**字符级 hex 编码**——`charCodeAt(i).toString(16)` 逐字符拼接，无 key、无混淆
- 保护类型：云锁 YunSuo 防红系统，`security_session_verify` cookie 三步挑战链
- 一句话概括：`srcurl = hex(完整URL)`、`security_verify_data = hex("宽,高")`，屏幕尺寸只要格式合法（实战随机 1400-1800×800-1200 即可）

## 逆向摘要

- 入口定位：首访收到 404-1.html 挑战页，页面源码**未混淆**——`stringToHex` 函数与 `YunSuoAutoJump` 流程直接可见
- 还原过程：
  1. 挑战页 JS：设 `srcurl=hex(url)` → `location.href = "/?security_verify_data=" + hex(screen.width+","+screen.height)`（50ms 定时器自动跳）
  2. 带参请求返回 404-2.html：删除 `srcurl` → 跳回原页，服务端 Set-Cookie `security_session_mid_verify`
  3. 第三次请求带齐两个 `security_session_*` cookie → 200
- JS→Python 差异：`hex(ord(c))[2:]` 与 `charCodeAt(i).toString(16)` 等价（均小写、省略前导 `0`），测试中曾误探索 base64 路线（早期 `test.js`，未随仓库保留），实际无编码

## 复现

```bash
# 依赖：无（标准库）
python main.py
```

- 样例输入 → 期望输出（3 组 hex 编码 + 1 组挑战参数集成验证，全部来自实战抓包）：

| 输入 | 期望输出 |
|------|---------|
| `"1440,810"`（屏幕数据） | `313434302c383130` |
| `"http://shyq.org.cn/"`（srcurl） | `687474703a2f2f736879712e6f72672e636e2f` |
| `"http://shyq.org.cn/list-yuqingdongtai.html"`（srcurl） | `687474703a2f2f...6d6c`（40 字符 URL → 80 hex） |

## 验证与实测

- 样例对比：4/4 通过（含 `build_challenge` 集成验证：`srcurl` + `security_verify_data` + 完整 `next_url` 生成）
- 真实请求验证：2025-08 `spider_SHYQ.py` 全站跑通（分类页 + 详情页 + 图片下载），挑战链：请求 → 随机屏幕尺寸 → 带参重试（≤3 次）→ 删 srcurl → 200

## 备注

- 失效风险：防护只校验 hex 格式与 cookie 完整性，不校验屏幕值真实性；若升级为加密挑战（观察挑战页是否含混淆 JS）需重新分析
- 坑：`srcurl` 编码的是**完整 URL**（含 `http://` 与结尾 `/`），少字符会导致校验失败；`security_verify_data` 只跟屏幕尺寸相关，与 URL 无关，同一值可复用
