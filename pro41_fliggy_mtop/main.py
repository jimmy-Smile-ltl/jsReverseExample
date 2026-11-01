"""
pro41 飞猪 MTOP 签名 — sign = md5(token & t & appKey & data)

复现飞猪 H5（market.m.taobao.com / h5api 网关）的 MTOP 标准签名（纯标准库）:

    sign = md5(f"{token}&{t}&{appKey}&{data}")      # 32 位小写 hex
    token = Cookie `_m_h5_tk` 第一个 '_' 之前的部分（32 位 hex）

握手规则: 首次请求不带 token/sign → 服务端下发 Set-Cookie `_m_h5_tk` 并返回
`FAIL_SYS_TOKEN_EMPTY::令牌为空`；用新 token 重发即 SUCCESS（token 约 1 小时轮换）。

关键点: 搜索结果类接口的 `data` 必须是 **args 包裹式** —— 外层 compact JSON，
内层 args 用**带空格**的 JSON（Python `json.dumps` 默认分隔符），平铺参数会返回
SUCCESS 但数据为空。

来源: 飞猪 H5 SPA（阿里 MTOP 同源小猪/淘宝 h5）
      2026-11-01 单会话真机抓包，3 组 SUCCESS 请求的 data/t/sign 全部对齐。
用法: python main.py
"""

import hashlib
import json
import time

APP_KEY = "12574478"
TTID = "201300@travel_h5_3.1.0"
HOST = "h5api.m.taobao.com"       # 飞猪 H5 走 taobao 网关；m.fliggy.com 返回 ILLEGAL_ACCESS
H5_VERSION = "2.23.11"

API_SRP = "mtop.trip.search.srp.pattern.render"   # 搜索结果（args 包裹式）
API_HOME = "mtop.fliggy.ssif.pattern.home"        # 首页猜你喜欢模块流


def md5_sign(token: str, t: str, data: str, app_key: str = APP_KEY) -> str:
    """MTOP 签名：token & 时间戳 & appKey & data，四段用 & 连接后 md5。"""
    return hashlib.md5(("%s&%s&%s&%s" % (token, t, app_key, data)).encode()).hexdigest()


def token_from_cookie(cookie: str) -> str:
    """从 Cookie 串里取 `_m_h5_tk` 的首段（`<token>_<expire_ms>`）。"""
    for part in cookie.split(";"):
        k, _, v = part.strip().partition("=")
        if k == "_m_h5_tk":
            return v.split("_")[0]
    return ""


def build_params(api: str, version: str, data: str, t: str, token: str = None) -> dict:
    """组装 query 参数；有 token 才带 sign（首次握手故意不带）。"""
    params = {"type": "originaljson", "data": data, "appKey": APP_KEY,
              "t": str(t), "ttid": TTID, "v": version}
    if token:
        params["sign"] = md5_sign(token, str(t), data)
    return params


def compact(obj) -> str:
    """JS JSON.stringify 等价（无空格）。"""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


# ---------------------------------------------------------------- 请求体构造
def search_data(keyword: str, page: int = 1, page_size: int = 20, **extra) -> str:
    """mtop.trip.search.srp.pattern.render 的 data：外层 compact + args 内层带空格。"""
    args = {"keyword": keyword, "pageNum": page, "pageSize": page_size,
            "spm": "181.27203027", "searchType": "product", "tabType": "ALL",
            "channel": "h5", "h5Version": H5_VERSION, "platform": "h5"}
    args.update(extra)
    return compact({"bizType": "search", "name": "fliggy_search_list",
                    "version": "1.0.0", "platform": "h5",
                    "args": json.dumps(args, ensure_ascii=False),
                    "isLocationPermission": False, "h5Version": H5_VERSION})


def feed_data(page: int = 1, tab_id: str = "1", req_time: str = None) -> str:
    """mtop.fliggy.ssif.pattern.home 的 data（首页猜你喜欢）。"""
    req_time = req_time or time.strftime("%Y-%m-%d %H:%M:%S") + ".000"
    args = {"source": "miniapp", "useNewTrackArgs": "1",
            "params": {"spmabc": "181.27203027.1998936340",
                       "fromType": "CombDxGuessLike", "initPageNo": 0,
                       "gulTabId": tab_id,
                       "algoParams": {"tabId": tab_id, "tabLevel": "1",
                                      "isTraveling": "false", "tabTypeInfo": "GUSSETAB",
                                      "appid": 16051, "lbsCity": "", "tabType": "ALL",
                                      "isPreloadTab": True, "isMainTab": True,
                                      "tairKey": "GULTAB_1_0_0_2_1",
                                      "selectedTab": int(tab_id)},
                       "pageNo": page}}
    return compact({"bizType": "homepage",
                    "name": "fliggy_home_guess_you_like_miniapp_new",
                    "version": "1.0.0", "platform": "h5",
                    "args": json.dumps(args, ensure_ascii=False),
                    "isLocationPermission": False,
                    "userFlowParam": json.dumps(
                        {"spmDetail": "181.27203027", "clientReqTime": req_time},
                        ensure_ascii=False),
                    "h5Version": "2.1.8"})


# ---------------------------------------------------------------- 样例验证
# 2026-11-01 同一会话的真机抓包（_m_h5_tk=4261493720cf51d32d9e70a6cc8545f9_...）
TOKEN = "4261493720cf51d32d9e70a6cc8545f9"

SAMPLE_CASES = [
    {"name": "SRP 搜索 云南 page=3", "api": API_SRP, "version": "1.0",
     "t": "1793514768474",
     "data": search_data("云南", page=3, page_size=5),
     "expected": "4d49ea199132bf434074c3f08474ddcf"},

    {"name": "首页 feed page=3", "api": API_HOME, "version": "1.0",
     "t": "1793514769427",
     "data": feed_data(page=3, tab_id="1", req_time="2026-11-01 14:32:49.000"),
     "expected": "8f07c471788d029b3866e19de3051470"},

    {"name": "SRP 搜索 大理 page=1", "api": API_SRP, "version": "1.0",
     "t": "1793514769717",
     "data": search_data("大理", page=1, page_size=5),
     "expected": "d4aea465c2214a191d55cd350e1dcd07"},
]


def main() -> None:
    passed = 0
    for case in SAMPLE_CASES:
        got = md5_sign(TOKEN, case["t"], case["data"])
        ok = got == case["expected"]
        passed += ok
        print("[%s] %-20s %s" % ("PASS" if ok else "FAIL", case["name"], got))
        if not ok:
            print("       期望: %s" % case["expected"])

    checks = [
        ("token 提取", token_from_cookie(
            "cna=abc; _m_h5_tk=%s_1793514768188; _m_h5_tk_enc=deadbeef" % TOKEN) == TOKEN),
        ("无 token 不带 sign",
         "sign" not in build_params(API_SRP, "1.0", "{}", "1")),
        ("URL 形态", "/h5/%s/%s" % (API_SRP, "1.0") ==
         "/h5/mtop.trip.search.srp.pattern.render/1.0"),
    ]
    ok = all(v for _, v in checks)
    passed += ok
    print("[%s] %s" % ("PASS" if ok else "FAIL",
                      " / ".join(k for k, v in checks if v)))

    total = len(SAMPLE_CASES) + 1
    print("\n%d/%d 通过" % (passed, total))
    if passed != total:
        raise SystemExit(1)


# ---------------------------------------------------------------- 可选: 真实请求
# 完整流程（需网络 + curl_cffi，不进入 main）:
#   1) POST https://h5api.m.taobao.com/h5/<api>/<version>?<build_params 无 token>
#      → ret=FAIL_SYS_TOKEN_EMPTY，Set-Cookie 下发 _m_h5_tk
#   2) token = token_from_cookie(cookie)；t = 当前毫秒；sign = md5_sign(token, t, data)
#   3) 同参数重发 → SUCCESS::调用成功
#   4) 翻页只改 data 里的 pageNum/pageNo；token 复用，约 1 小时后轮换
# 请求头: UA 移动端 + Referer https://market.m.taobao.com/ + Origin 同域。
# 成品客户端: spider research/OTA 在线旅游/fliggy/fliggy_mtop.py（curl_cffi impersonate=chrome）

if __name__ == "__main__":
    main()
