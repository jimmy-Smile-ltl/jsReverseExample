# 百度指数 — 指数数据解密: 单表替换密码

> 复现对象：`无限集数/其他/百度指数/`（index.py + test.ipynb）· 技术分类：`encrypt` · 状态：✅ 可复现（7/7 通过，2026-08-20 验证）

## 站点与目标

- 站点：`https://index.baidu.com/`（百度指数，需要登录态 cookie）
- 目标接口：`GET https://index.baidu.com/api/SearchApi/index?area=&word=&startDate=&endDate=` 返回的 `data.userIndexes[].{all,pc,wise}.data`（**密文**）
- 配套接口：`GET https://index.baidu.com/Interface/ptbk?uniqid={uniqid}` 返回 `data` = 解密钥匙（ptbk）
- 反爬：`Cipher-Text` header（登录态 base64，未逆向）+ Cookie，过期时手动提供（原项目 `input()` 兜底）

## 技术要点

- 算法：**单表替换密码**——ptbk 前后各半：前半 = 密文字母表，后半 = 明文字母表，逐字符替换
- 混淆情况：无 JS 混淆；前端 decrypt 函数极简（test.ipynb cell 9 摘录的 for 循环版）
- 一句话概括：**index_data 每个字符在 ptbk 前半查表替换为后半对应字符**，输出逗号分隔数字串；`",,"` 空段 = 该日无数据 → 0

## 逆向摘要

- 入口定位：抓包对比明文与响应，发现 `data` 字段全字符在 15 字符表内循环出现（`r3`/`jr`/`ur`/`55` 等重复模式）→ 单表替换特征；`uniqid` 关联的 ptbk 接口即钥匙
- 还原过程：
  1. 统计响应字符集 = 15 个符号 → 与 ptbk 前半完全一致，后半 15 字符即明文表
  2. `decrypt = dict(zip(ptbk[:n], ptbk[n:]))`，逐字符替换得到数字串
  3. notebook 输出字符数组 `'1','0','9',',','1','2','1'...` 与还原结果逐字一致（2022-12-15）
- JS→Python 差异：无（纯字符串操作）；`e.split("")` 注意需逐字符而非按码点（ptbk 全 ASCII，无差异）

## 复现

```bash
# 依赖: Python 标准库 (0 第三方)
python main.py   # 真实三元组 + roundtrip×3 + 空值处理 (纯 Python, 无网络)
```

| 输入 | 期望输出 |
|------|---------|
| ptbk=`WMmOaR5u3xjqerN.9-%48617205+,3`, 密文 777 字符 | 明文 `109,121,174,...` 数字串, sha256 `d52ab791...9b49` |
| 明文 → encrypt → decrypt | 还原 == 原明文（3 组，含 2022-12-08 真实 30 天序列 832..984） |
| 明文含 `",,"` 空段 | typeChange 空段转 0 |

## 验证与实测

- 样例对比：7/7 全部通过（2026-08-20）；真实三元组期望值 = notebook 当日输出（2022-12-15）
- 真实请求：原项目 2022-12 实爬 10 年×多城市数据（环境污染/雾霾，output.json 存 30 天结果）；本仓库未做网络复测（需有效登录 cookie + Cipher-Text）
- 失效风险：ptbk 每次请求动态生成（uniqid 关联），但替换逻辑不变；`Cipher-Text` 未逆向，登录过期后需手动提供

## 备注

- `Cipher-Text` header（约 1.2KB base64，含时间戳对 `1670659591568_1670660090319`）未逆向——不影响解密算法复现，但影响真实请求成功率
- 空值是服务端数据本身的问题（原项目注释确认），非解码错误
