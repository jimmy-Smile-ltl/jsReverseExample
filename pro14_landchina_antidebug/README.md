# 中国土地市场网 — CloudWAF 行为画像 + disable-devtool v0.3.8 + Hash 头签名

> 复现对象：`spider research/其他/pro25 中国土地市场网 反调试/` · 技术分类：`waf` + `debug` · 状态：✅ 可复现（34/34 通过，2026-08-19 验证）

## 站点与目标

- 站点：`https://www.landchina.com/`（中国土地市场网，Vue2 + Element UI，原项目 2026-06-30 分析）
- 加密参数：请求头 `Hash = MD5(userAgent + dayOfMonth + URL最后一段)`（app.js 拦截器生成，**后端不校验**）
- 目标接口：`POST https://api.landchina.com/tGdxm/result/list`（供地结果列表，pageNum/pageSize/xzqDm/gyFs/tdYt/startDate/endDate）

## 技术要点

- 核心反爬：**华为云 CloudWAF**（Server: CW + HWWAFSESID/HWWAFSESTIME cookie + 418 拦截页）——渐进式行为画像，非浏览器 TLS 指纹 2-3 次请求后 IP 级封锁
- 辅助：disable-devtool v0.3.8（开源库 theajack，7 种检测器轮询）；`console.log = () => {}` 屏蔽
- 一句话概括：前端签名是摆设，真正的墙是 CloudWAF 行为画像——需要 curl_cffi 浏览器 TLS 指纹 + 代理轮换

## 逆向摘要

- 入口定位：抓包发现 `Hash` 头 + 418 拦截页 → 分析 `chunk-vendors.js`（Vue+Element+disable-devtool+MD5+axios）→ app.js 拦截器源码定位 Hash 公式
- 还原过程：
  1. `r = e.url.split("/"); t["Hash"] = MD5(UA + new Date().getDate() + r[r.length-1])`——**dayOfMonth 无前导零**，路径取最后一段（`tGdxm/result/list` → `list`）
  2. CloudWAF 事件ID `{risk}-clou-{node}-{ts}-{hash}`：`08-clou-37` 低风险放行 → `90-clou-37` 行为画像 418 → `90-clou-90` IP 确认封锁
  3. 反调试按报告还原：Debugger>100ms / DateToString、FuncToString 调用≥2 次 / Size 用 `innerWidth * devicePixelRatio` 补偿浏览器缩放 / DebugLib 查 `eruda`、`_vcOrigConsole`
  4. 站点配置 `detectors [0,1,3,4,5,6,7]` **唯独禁用 Size**，且库可能未激活（未找到全局对象）——纯前端手段对爬虫无意义
- 坑：抓 `chunk-vendors.js` 时被 WAF 拦下，保存下来的其实是 **418 拦截页**（本仓库原样留存为证据，文件名未改）；报告 Hash 示例 `c9bf226a` 的 UA 被截断无法复现，样例改用全量 UA 公式自洽计算

## 复现

```bash
# 依赖: Python 标准库 (0 第三方, 无需 node/网络)
python main.py            # 34 项: 拦截页/事件ID/风险演变/Hash/反调试判定
python main.py --live     # 追加单次真实请求验证 WAF (会标记本机 IP, 慎用)
```

| 验证项 | 结果 |
|--------|------|
| 418 拦截页证据解析 ×2（chunk-vendors.js 内含 CloudWAF 标记 + 事件ID） | ✅ |
| 事件ID 解析 ×3 / 非法格式拒绝 ×3 / 风险演变 3 阶段 ×3 | ✅ |
| Hash 样例 ×4（含绝对 URL 提取）/ 32 hex / 无前导零 / 末段提取 | ✅ |
| 检测器表 0-7 + 站点配置（禁用 Size）×2 | ✅ |
| Size(含 dpr 缩放补偿)/Debugger/toString/Performance/DebugLib 判定 ×16 | ✅ |
| onDevToolOpen 行为兜底（close→500ms→404.html）×1 | ✅ |

## 验证与实测

- 样例对比：34/34 通过；拦截页事件ID与报告阶段 1 抓包值逐位一致；Hash 与公式自洽（2026-08-19）
- 真实请求验证：原项目 2026-06-30 CloakBrowser 实测——真实浏览器跨域 XHR 也被 418（WAF 不信任会话）；curl/requests 2-3 次后 IP 标记，`python main.py --live` 可现场复测 WAF 响应特征

## 备注

- 失效风险：CloudWAF 规则随时调整；disable-devtool 精确阈值未留存（源码未捕获，判定按报告文档还原）；Hash 后端不校验，失效也不影响取数
- 绕过：curl_cffi（`impersonate="chrome120"`）+ 住宅代理轮换，或 Playwright 建信任再调 API；被封锁 IP 需数小时恢复，务必低频（1-2 req/s）
- 关联：本仓库 `pro01`（加速乐 521）/`pro02`（云锁）/`pro03`（阿里云 acw_sc__v2）均为 WAF 逆向的姊妹案例
