# 抖音 a_bogus 签名 — SDK VM + SM3/RC4 变体

> 复现对象：`经典 不开源/抖音-a_bogus签名-2026-08-30` · 技术分类：`vm` `encrypt` · 状态：✅ 可复现（离线 3/3；Node 对拍 16/16；线上 3/3，2026-08-30）

## 站点与目标

- 站点：`https://www.douyin.com/`（webmssdk，2026-08 版）
- 加密参数：Query `a_bogus`（~196 字符，base64 混合字符集）
- 目标接口：作品列表 / 搜索 / 详情等 XHR；GET 与 POST body 均参与签名

## 技术要点

- 保护类型：字节自研 SDK VM（`_$webrt_` 解释器执行字节码，XHR/fetch 拦截自动签名）
- 算法组成：SM3（国密）+ RC4 变体混淆（`ab_arr_256` / `ua_arr_256`）+ 双字母表自定义 Base64
- 结构：`topHeaderRandom(4) + ABgarbled(29 值流 + 随机填充 + 末位 XOR 校验)`；填充位服务端不校验

## 逆向摘要

- 入口定位：hook `XMLHttpRequest` 的 `open/send`，回溯到 SDK 的 fetch 拦截器；再定位 `getABogus` 导出
- 还原过程：
  1. 不补整个 SDK（UMD/iframe/ECDH/canvas 七层墙），只提取 485 行纯函数 `getABogus`
  2. 对拍：Node 注入 mulberry32 + 固定 `Date.now`，Python 同 PRNG 逐函数移植，16/16 逐字节一致
  3. 结构拆解：`arr29` = 时间/参数/body/UA 的 SM3 摘要 + `arr2` 50 项置换 + 随机填充
  4. 传输层：`ab_garbled` 对 29 值流做 RC4 变体异或；UA 单独走 `ua_garbled` + 第二字母表
- JS→Python 差异：`encodeURIComponent` 逐字符转字节（非 UTF-8 整体）；`Math.imul` / ToInt32 截断；随机调用顺序必须守恒

## 复现

```bash
# 仅标准库
py main.py     # SM3 标准向量 + 3 组固定 PRNG/时间戳签名
```

| 输入 | 期望输出 |
|------|---------|
| GET `device_platform=webapp&aid=6383&...&version_name=29.1.0` | 196 字符，`my0jDFSw...Oo5Bj==` |
| GET `aid=6383&keyword=food+review&max_cursor=0&count=18` | 196 字符，`my0jDFSw...Oo5VD==` |
| POST `aid=6383&count=18`，body `{"keyword":"food","page":1}` | 196 字符，`my0jDFSw...Oo5Ej==` |

## 验证与实测

- 离线：`py main.py` 3/3 通过；SM3("abc") 国密标准向量通过
- 对拍：`reference/parity_harness.js` 注入随机源，4 输入 × 4 种子 = 16/16 与 Python 逐字节一致
- 线上：2026-08-30 实测 3/3 `status_code=0`；msToken 已非必需（SDK 升级后接口放开）

## 备注

- 失效风险：SDK 升级可能改字母表/结构；旧 196 字符格式服务端仍向后兼容
- 坑：确定性补环境（`Math.random=0.5`）会让随机填充位恰为 0，看似“无随机”；必须用真随机环境做差分
- 样例参数中的用户 ID 已脱敏，签名仅用于离线算法比对，不能用于真实请求
- 第三方文件：`reference/sign_engine.js` 为 a_bogus 签名函数提取/移植版，版权归字节跳动，仅作学习研究归档
