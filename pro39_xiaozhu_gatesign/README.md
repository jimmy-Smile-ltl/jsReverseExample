# 小猪民宿 gatesign — HMAC-SHA1(排序参数串, md5(url))

> 复现对象：`spider research/OTA 在线旅游/xiaozhu/gate.py` · 技术分类：`encrypt` · 状态：✅ 可复现

## 站点与目标

- 站点：https://m.xiaozhu.com（H5 外壳）· https://minsu.xiaozhu.com（民宿 SPA）
- 加密参数：`gatesign`（40 位小写 hex，40 字节；**目前网关收而不硬校验**）
- 目标接口：`GET https://wirelesspub-lodge.xiaozhu.com/search/result`（房源搜索，`cityId/checkInDay/offset/length`）

## 技术要点

- 算法/保护类型：HMAC-SHA1，密钥是 `md5(url)`，消息是「URL + 排序后的 URL 编码参数串」
- 混淆情况：两份 webpack 产物（app 主包 255KB + minsu SPA 598KB），字符串数组带 rotation IIFE
- 一句话概括：`sig = HmacSHA1(url + '?' + sorted(k=v), md5(url))`，编码后再做 6 组可读化替换

## 逆向摘要

- 入口定位：抓包发现 `gatesign`，直接在 `minsu.xiaozhu.com/assets/index-*.js` 里搜 `gatesign=` 命中 `pI()`
- 还原过程：
  1. 消息 = `url(不含 query) + '?' + '&'.join(sorted("k=encodeURIComponent(v)"))`；单引号额外编码成 `%27`
  2. 编码后对**整条消息**做替换链：`%3A→:` `%2C→,` `%5D→]` `%5B→[` `%20→+` `%40→@`（顺序敏感）
  3. 密钥 = `md5(url)` 的 32 位 hex，直接当 HMAC 的 key（不是 hex 解码）
  4. **两套调用约定**：m.xiaozhu 主包参数里没有 `gatesign` 键；minsu SPA 带 `gatesign=""` 空占位且**参与排序**——消息串差一个 `gatesign=`，签名就不同
- 取证：运行时改写 SPA bundle，在 `pI()` 里插桩打印 `(url, msg, key, out)`，一次拿到四元组；Python 用同 `(msg,key)` 算出的值与 `out` 全等

## 复现

```bash
# 依赖: 仅标准库 (hashlib / hmac / urllib)
python main.py
```

| 输入（2026-10-31 真实抓包） | 期望 gatesign |
|------|---------|
| A：m.xiaozhu 首页配置（参数无 gatesign） | `de985828dbe983d299c75fbe48134e7cd3f2fcc6` |
| A：m.xiaozhu 搜索列表 | `9c51af8e25cbd3f40969cb89a76f033f07011239` |
| B：minsu 地区地标（`gatesign=""` 占位） | `96d5dc6bd3e420e5b99e8af966c8a5078aee77d3` |
| B：聚合筛选（`timezone=+08:00` 触发 `%3A→:`） | `e8ea94c44bc5b5ca091fcd7f10cbd68945b16ddf` |
| B：搜索列表（多 `localSelected/roottype` 两键） | `bbcddbf73477c3e35106054c8b129e5551e4776e` |

## 验证与实测

- 样例对比：5/5 全部通过，另有 `sign_url` 回填自检 1 组（共 6/6）
- 取证总量：18 组真值（2 组主包约定 + 10 组真实请求 + 5 组插桩 `msg/key/out` + 1 组交叉）全等
- 真实请求验证：2026-10-31 `curl_cffi` 无 Cookie 直连搜索接口 `status=200, count=900`（北京），翻页正常

## 备注

- 失效风险：接口**当前不强制校验** gatesign（全 0 或整段删除仍 200 同样数据），算法留着防站点收紧；登录/下单/风控域可能另有校验
- 坑一：两套约定必须按来源区分——看 URL 里 `gatesign` 的位置（**末尾**=主包无占位，**中段**=SPA 有空占位），抓包的 `referer` 也能直接指明
- 坑二：`gatets` 主包是秒、SPA 是毫秒，服务端不校验精度，照抄对应客户端即可；替换链必须在**整条消息**上做，只处理 value 会漏掉 URL 里的字符
