# spa14.scrape.center — WASM 签名逆向（教学案例）

> 复现对象：`spider research/其他/pro24 scrape wasm/` · 技术分类：`wasm` · 状态：✅ 可复现（10/10 通过，含真实 WASM 交叉验证）

## 站点与目标

- 站点：`https://spa14.scrape.center/`（Scrape Center 系列靶场）
- 加密参数：`GET /api/movie/` 的 `sign`（另含 `limit`/`offset`）
- 目标接口：电影列表 API；`sign = offset + timestamp//3 + 16358`

## 技术要点

- 算法：**WASM 导出函数** `encrypt(offset, ts) = offset + ts/3 + 16358`（232 字节无保护）
- 保护类型：WASM 隔离算法（教学靶场）；JS 侧 `this.$wasm.asm.encrypt(n, timestamp)`，`n=(page-1)*limit`，`timestamp=Date.now()/1000`
- 一句话概括：教科书级 WASM 流程——**wasm2wat 反汇编直出公式**，先评估再决定是否值得深入（几百 KB 的 Rust 大 WASM 就该考虑 wasmer 直接调用）

## 逆向摘要

- 入口定位：抓包见 `sign` → 搜索 `sign:` 命中 chunk 中 `encrypt` 调用 → 网络面板定位 `Wasm.wasm`（232 字节）
- 还原过程：
  1. `wasm2wat Wasm.wasm` → 导出 `encrypt` 函数体仅 4 条指令：`local.get 0, local.get 1, i32.const 3, i32.div_s, i32.add, i32.const 16358, i32.add`
  2. **关键点**：`i32.div_s` 是有符号整除（Python 用 `//` 需注意负数时间戳边界；对正常时间戳两者一致）
  3. Python 一行公式即完成还原；**交叉验证**：Node `WebAssembly.Instance` 实跑原 .wasm，4 组输入逐值一致
- 附带文件：`Wasm.wasm`（232B 原文件）+ `Wasm.wat`（反编译产物），用于复现完整流程

## 复现

```bash
# 依赖: Python 标准库; --wasm 交叉验证需本机 node
python main.py            # 6 项样例验证 (无需网络)
python main.py --wasm     # 追加 4 组 Node 实跑 Wasm.wasm 比对
```

| 验证项 | 结果 |
|--------|------|
| 固定样例 ×4（offset 0/90/990 + 整除进位边界） | ✅ |
| 参数组装 ×1（page → limit/offset/sign 结构）/ 负 offset ×1 | ✅ |
| Node 实跑 Wasm.wasm 交叉 ×4（与真实 WASM 逐值一致） | ✅ |

## 验证与实测

- 样例对比：10/10 通过；4 组样例经 Node 实跑原 `.wasm` 确认与真值一致
- 真实请求验证：原项目爬虫已跑通全站 80 页（sign 被服务器接受）；本仓库 `--wasm` 模式即为无网络自证

## 备注

- 教学价值：完整演示"WASM 逆向四步"——抓包定位 → 提取 .wasm → wasm2wat → 公式还原；对比 pro15/pro16（数百 KB Rust 大 WASM）可见"小 WASM 反汇编 / 大 WASM 调运行时"的分流决策
- 坑：`i32.div_s` 负数整除向零截断（Python `//` 向下取整，负数时间戳场景需注意，本靶场无实际影响）
