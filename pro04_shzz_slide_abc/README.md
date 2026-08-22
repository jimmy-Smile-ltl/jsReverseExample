# 中国社会组织政务服务平台 — 滑块验证码 a/b/c 参数加密

> 复现对象：`无限集数/政府平台/中国社会组织政务服务平台/` · 技术分类：`encrypt` `captcha` · 状态：✅ 可复现（样例全部通过）

## 站点与目标

- 站点：`https://xxgs.chinanpo.mca.gov.cn/`（民政部社会组织信用信息公示，2024-07 实测）
- 加密参数：搜索接口 `gridQuery.html` POST 数据中的 `a`、`b`、`c`（滑块验证通过后下发）
- 目标接口：`/gsxt/PlatformSHZZFRKGSXT/slideCaptcha`（发滑块）、`slide_captcha_check`（校验）、`biz/ma/shzzgsxt/a/gridQuery.html`（数据）

## 技术要点

- 算法：`newA = base64(a)`、`newB = base64(b)`（服务端随机串仅再编码）；`newC = base64(base64(RSA-1024 PKCS1v15(移动距离)))`——**RSA + 双重 base64 嵌套**
- 保护类型：滑块验证码；距离服务端校验（`slide_captcha_check` 返回 code==200 才有效）
- 一句话概括：加密无 JS 混淆，难点在缺口距离识别（OpenCV 模板匹配）与校验重试（距离偶发不准，10 次内成功）

## 逆向摘要

- 入口定位：搜索接口 POST 需 a/b/c 参数 → 前端 JS 定位 `slideCaptcha` 接口与加密逻辑 → 确认 c 是 RSA 公钥加密
- 还原过程：
  1. `slideCaptcha` 返回 `{a, b, c:{cutImage, oriImage}}`——a/b 每次请求随机，图片为 base64 PNG
  2. 缺口识别：`cv2.matchTemplate(原图, 缺口图, TM_CCOEFF_NORMED)` 最佳匹配 x 坐标即移动距离（滑块缺口图 40×50 左右）
  3. RSA 加密距离字符串：1024-bit 公钥 PKCS#1 v1.5（原项目 python `rsa` 库 = pycryptodome `PKCS1_v1_5` 完全兼容），密文固定 128 字节
  4. 关键细节：**双重 base64**——`rsa.encrypt` 后先 b64encode 一次，再 b64encode 一次（128B → 172 字符 → 232 字符）
  5. 校验通过后 gridQuery POST 携带 `a=newA, b=newB, c=newC`，失效（`check` 非 200）则重新走全流程

## 复现

```bash
pip install pycryptodome          # 必需（RSA）
pip install opencv-python         # 可选（缺口识别 find_gap）
python main.py
```

- 样例验证（无需网络）：
  - a/b base64 可逆性 ×3（a/b 为服务端随机下发串，未留存历史值，以编码可逆验证）
  - RSA 密文结构 ×3（232/172/128 字符/字节固定链）+ 随机填充性质（相同输入两次密文不同）
  - 真实抓包图片 `cutImage.txt`/`oriImage.txt` 为合法 PNG（2024-07 留存）
  - 缺口识别（有 opencv 时）：真实图片上 matchTemplate 出距离

## 验证与实测

- 样例对比：全部通过（结构验证 + 可逆验证；RSA 随机填充无法固定期望值，以长度链与性质验证）
- 真实请求验证：2024-07 全量爬取 3000+ 关键词（省/市/县行政区划 × 组织状态），滑块校验有效期内复用 a/b/c，失效自动刷新重试

## 备注

- 失效风险：RSA 公钥若更新需重新提取（公钥内嵌于前端 JS）；滑块距离识别偶发偏差导致校验失败，重试即可
- 坑：c 的双重 base64 极易漏一层（漏一层服务端解码失败）；距离必须是整数像素串（`str(length)` 不能带浮点）；`slideCaptcha` 与 `check` 均需带上站 Cookie（`https_waf_cookie` 等）
