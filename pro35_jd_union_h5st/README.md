# 京东联盟 h5st 签名 — stack VM + 双重乱序编码

> 复现对象：`经典 不开源/京东联盟-h5st签名-2026-08-30` · 技术分类：`vm` `encrypt` · 状态：✅ 可复现（离线 3/3；与 SDK 逐字节一致 10/10 段，2026-08-30；线上待复测）

## 站点与目标

- 站点：`https://union.jd.com/`（`js_security_v3.js`，2026-08 版）
- 加密参数：Query `h5st`（10 段 `;` 分隔，共 1103 字符）
- 目标接口：联盟商品搜索 `unionSearchRecommend`（`functionId` 参与签名）

## 技术要点

- 保护类型：236KB stack VM（5209 条字节码 + 374 项字符串表 + XOR 字符串混淆）+ 内联 CryptoJS
- 编码层：自定义 base64 字母表 + `rev3`（3 字节块序反转）+ `rev4`（4 字符组内逆序）
- 关键结论：段⑧ 名为“加密”，实为 **JSON → PKCS7 → rev3 → customB64 → rev4**，全程无密码学

## 逆向摘要

- 入口定位：VM 解释器的调用分发器即 `Function.prototype.call`；替换全局 `call` 零插桩拦截全部调用
- 还原过程：
  1. hook `call` 捕获 `test`（X/ts19/rd）与 `parse`（待签名串）→ 得到 seg5/seg9 的拼接材料
  2. seg8 先按「配对正确性 → 自定义编码 → 块置换」顺序拆，最后才确认没有加密算法
  3. 同 run 注入对齐参数（时间/随机/盐），Python 与 Node 输出逐段 diff 全绿
  4. `seg10 = rev4(customB64(rev3("appid,body,functionId"+b"\x03"*3)))`，恒定常量
- JS→Python 差异：`body_json` 必须紧凑 JSON；seg8 的 env JSON 必须 2 空格缩进；哈希用标准 `hashlib.sha256`（联盟 SDK 非变体）

## 复现

```bash
# 仅标准库
py main.py     # 3 组确定性向量：materialId/时间戳不同，固定盐与随机串
```

| 输入 | 期望输出 |
|------|---------|
| `materialId=13884, ts13=1788024996282, ts19=20260830123456789` | 1103 字符，seg5 `85d09eab...` |
| `materialId=10086, ts13=1788025000282, ts19=20260830123500789` | 1103 字符，seg5 `ba51bdd2...` |
| `materialId=2024, ts13=1788025016282, ts19=20260830123655789` | 1103 字符，seg5 `0b72d733...` |

## 验证与实测

- 离线：`py main.py` 3/3 通过；三段长度均为 `[17,16,5,92,64,3,13,788,64,32]`，seg10 恒为常量
- SDK 对比：2026-08-30 同 run 注入参数，Python 与补环境输出 10/10 段逐字节一致
- 线上：原项目记录「线上实测待复测」；本仓库未做真实请求（TLS 指纹 + 登录态依赖）
- 参考脚本：`reference/compare_python.js`（同 run 逐段 diff；依赖的 `sign.js` 未随仓库分发）

## 备注

- 失效风险：SDK 版本随联盟页面轮换；seg8 env 的 `ls/wk/bu*` 随浏览器环境变化
- 坑：跨 run 对比会被时间/随机值污染，必须同 run 注入；`salt = 7 随机字符 + "RvI<7|"`
- 样例 fp/token/canvas/webglFp 均为占位值，不可用于真实请求
