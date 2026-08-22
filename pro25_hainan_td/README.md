# 海南航空 TrustDecision blackBox — payload 解析与会话密钥恢复

> 复现对象：`spider research/机票/pro5 海南航空/pro4_pure_http/` · 技术分类：`wasm encrypt env` · 状态：🔒 仅样例（key 恢复链路 ✅，field2 加密未还原）

## 站点与目标

- 站点：new.hnair.com（海航官网机票搜索，需 TrustDecision 指纹才可通过风控）
- 加密参数：`blackBox`（请求头 `tdid`/正文参数，TrustDecision DeviceFingerprintJs SE v4.2.2 生成）
- 目标接口：`POST https://new.hnair.com/hainanair/ibe/api/air/searchResults.do`

## 技术要点

- 算法/保护类型：WASM 指纹采集（`b.s` 114 项环境指纹）→ protobuf 风格 payload → wasm func 193 生成会话 key → AES 密文 → url-safe base64
- 混淆情况：JS 控制流平坦化 + 自定义命名（`QOoQQQ`/`O0Q0oo`/`wfb`）；核心逻辑在 wasm 内
- 一句话概括：`blackBox = btoa_urlsafe(指纹 payload)`，其中 payload.field2 为 AES 密文、field3 尾部 35B 为会话 key 字符 XOR 固定 9 字节周期流 `anairhain`

## 逆向摘要

- 入口定位：抓包发现 `blackBox` → XHR 断点回溯到 `getDeviceInfo` → `QOoQQQ`（组装 payload）→ `wfb`（wasm func 193）
- 还原过程：
  1. `WebAssembly.instantiate` hook 拿到 import 对象（20 函数）：`q=Math.random`（35 个 f64）、`d=partner`（"hainanair"）、`p=appKey`、`s=version`、`t=clientId` 等
  2. 反汇编 wasm func 193 确认 key 派生：`key[i] = alphabet[trunc(f64[i]*62) % 62]`，写入字段缓冲 offset 13（即 field3 = 13B 头部 + 35B key）
  3. 注入脚本固定 `Math.random=0.5` → 捕获 key=`s`×35；对同次运行 payload 做 `P[i] = 's' ^ tail[i]` 推出固定 XOR 流 P（周期 9 = `anairhain`）
  4. 用 P 对 4 组真实随机 payload 反推 key，35 字符全部落在 62 字母表内 → 机制确认
  5. field2（115×16B）为 AES 密文，但 key 的最终 AES 派生方式（ascii/hash/索引等候选均未命中）未还原 → 全链路 🔒

## 复现

```bash
# 依赖: 仅标准库 (binascii)
python main.py
```

- 样例输入 → 期望输出（内置在 `SAMPLE_CASES`，5 组，2026-06 抓包）：

| 输入（payload，内嵌 hex） | 期望输出（恢复的 35 字符 key） |
|------|---------|
| cap9 固定随机运行 1817B | `s`×35（Math.random=0.5 的确定性结果） |
| cap7 固定随机运行 1817B | `s`×35 |
| cap3 真实运行 1929B | `dOVD4uVbCcLDMFSzk5k8oWIjhJ0GpL6EcWT` |
| cap4 真实运行 1929B | `35DhGeCLxL7Uz4IYlSAO6nxonANxX0dHdTe` |
| cap5 真实运行 1913B | `xqsWebHm8XfsoS6thWlU5Zr1EwEJAX6wqlJ` |

## 验证与实测

- 样例对比：5/5 全部通过（key 恢复链路确定性验证完成）
- 真实请求验证：2026-06 海航官网真实请求获取原始 blackBox 并解析成功；未验证重新生成合法 blackBox 发包（field2 加密未还原）

## 备注

- 失效风险：SDK 升级后算法变更；field3 头部 13B 含义与 field2 AES key 派生方式待继续逆向（wasm func 193 调用链：`call 38/32/44/50/30` 等）
- 坑：`bytes(cycle(P))` 对无限迭代器求值会挂死；minified JS 中 regex 字面量会破坏括号平衡扫描器，注入代码必须实测 `node --check`
