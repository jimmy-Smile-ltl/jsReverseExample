"""
pro39 小猪民宿 gatesign — HMAC-SHA1(排序参数串, md5(url))

复现 wirelesspub-*.xiaozhu.com 网关签名 gatesign（纯标准库）:

    key       = md5(url_without_query)                       # 32 位小写 hex
    msg       = url_without_query + '?' + '&'.join(sorted(k=v))
    gatesign  = HMAC-SHA1(msg, key)                          # 40 位小写 hex

    v 的编码 = encodeURIComponent(v).replace("'", "%27")，再对整个 msg 做替换:
               %3A→:  %2C→,  %5D→]  %5B→[  %20→+  %40→@

两种调用约定（同一算法，区别只在 gatesign 空位参不参入排序）:
    约定 A  placeholder=False  m.xiaozhu.com 的 H5 外壳 —— 参数里根本没有 gatesign 键
    约定 B  placeholder=True   minsu.xiaozhu.com 的 SPA —— 带 gatesign="" 占位并参与排序

来源: secure.js（app bundle 的 it.verify）与 minsu index-C0RZyUpK.js 的 pI()，
      2026-10-31 用「函数插桩 + 真实请求」双路取证，20 组真值全部对齐。
用法: python main.py
"""

import hashlib
import hmac
from urllib.parse import parse_qsl, quote

# JS 替换表，顺序敏感（先编码再整体替换）
REPLACEMENTS = [("%3A", ":"), ("%2C", ","), ("%5D", "]"), ("%5B", "["),
                ("%20", "+"), ("%40", "@")]
SAFE = "!*'()"          # encodeURIComponent 保留不转义的字符


def encode_value(v) -> str:
    """JS FA()/ot(): encodeURIComponent(v).replace(/'/g, '%27')。"""
    if isinstance(v, bool):
        v = "true" if v else "false"
    elif v is None:
        v = ""
    return quote(str(v), safe=SAFE).replace("'", "%27")


def normalize(msg: str) -> str:
    """对整条消息做 URL 可读化替换（JS replace 链）。"""
    for a, b in REPLACEMENTS:
        msg = msg.replace(a, b)
    return msg


def build_message(url: str, params: dict, placeholder: bool = True):
    """返回 (待签消息, HMAC 密钥)。url 必须不含 query。"""
    p = {k: v for k, v in params.items() if k != "gatesign"}
    if placeholder:
        p["gatesign"] = ""                       # SPA 的空占位参与排序
    pairs = sorted("%s=%s" % (k, encode_value(v)) for k, v in p.items())
    msg = normalize(url + "?" + "&".join(pairs))
    key = hashlib.md5(url.encode("utf-8")).hexdigest()
    return msg, key


def sign(url: str, params: dict, placeholder: bool = True) -> str:
    """返回 40 位 hex gatesign。"""
    msg, key = build_message(url, params, placeholder)
    return hmac.new(key.encode("utf-8"), msg.encode("utf-8"),
                    hashlib.sha1).hexdigest()


def sign_url(url: str, params: dict, placeholder: bool = True):
    """返回 (带签名的 query string, gatesign)，参数顺序保持原样。"""
    sig = sign(url, params, placeholder)
    pairs = [("%s=%s" % (k, encode_value(v))) for k, v in params.items()]
    if "gatesign" in params:
        pairs = [p if not p.startswith("gatesign=") else "gatesign=" + sig
                 for p in pairs]
    else:
        pairs.append("gatesign=" + sig)
    return "&".join(pairs), sig


# ---------------------------------------------------------------- 真实样例
# 2026-10-31 抓包真值: query 即线上实际请求串（gatesign 为服务端已接受的值）
SAMPLE_CASES = [
    {"name": "A m.xiaozhu 首页配置", "placeholder": False,
     "url": "https://wirelesspub-search.xiaozhu.com/app/xzfk/html5/500/settings/html5HomePage",
     "query": "cityId=12&typeChannel=MWebSite&clientVersion=500&clientFrom=html5"
              "&gatets=1793452374&wttXMuWwbC=&ATNgmRNkrw="
              "&gatesign=de985828dbe983d299c75fbe48134e7cd3f2fcc6",
     "expected": "de985828dbe983d299c75fbe48134e7cd3f2fcc6"},

    {"name": "A m.xiaozhu 搜索列表", "placeholder": False,
     "url": "https://wirelesspub-lodge.xiaozhu.com/search/result",
     "query": "cityId=12&checkInDay=&checkOutDay=&offset=0&length=10&client=html5"
              "&role=xzfk&clientVersion=500&clientFrom=html5&gatets=1793452374"
              "&wttXMuWwbC=&ATNgmRNkrw="
              "&gatesign=9c51af8e25cbd3f40969cb89a76f033f07011239",
     "expected": "9c51af8e25cbd3f40969cb89a76f033f07011239"},

    {"name": "B minsu 地区地标", "placeholder": True,
     "url": "https://wirelesspub-lodgeunitbusiness.xiaozhu.com/app/xzfk/html5/600/global/areaandlandmark",
     "query": "clientFrom=html5&clientVersion=500&gatets=1793452530017&wttXMuWwbC="
              "&ATNgmRNkrw=&gatesign=&xzToken=&userId=&sessId=&ticket="
              "&cityId=12&bizType=1",
     "expected": "96d5dc6bd3e420e5b99e8af966c8a5078aee77d3"},

    {"name": "B 聚合筛选（timezone 触发 %3A→:）", "placeholder": True,
     "url": "https://wirelesspub-search.xiaozhu.com/app/xzfk/html5/500/search/getAggregateFilter",
     "query": "ATNgmRNkrw=&bedNum=&bundleType=app&checkInDay=2026-10-31"
              "&checkOutDay=2026-11-01&cityId=12&cityName=%E5%8C%97%E4%BA%AC"
              "&clientFrom=html5&clientVersion=500&distId=&facilitys=&gatesign="
              "&gatets=1793452609797&guestNum=&huXing=&keyword=&latitude=&leaseType="
              "&locId=&locLatitude=&locLongitude=&locName=&lodgeUnitTags=&longitude="
              "&maxPrice=&minPrice=&nation=0&orderBy=recommend&radius=5&role=xzfk"
              "&sessId=&ticket=&timezone=%2B08:00&userId=&wttXMuWwbC=&xzToken=",
     "expected": "e8ea94c44bc5b5ca091fcd7f10cbd68945b16ddf"},

    {"name": "B 搜索列表（新增 localSelected/roottype）", "placeholder": True,
     "url": "https://wirelesspub-lodge.xiaozhu.com/search/result",
     "query": "ATNgmRNkrw=&bedNum=&bundleType=app&checkInDay=2026-10-31"
              "&checkOutDay=2026-11-01&cityId=12&cityName=%E5%8C%97%E4%BA%AC"
              "&clientFrom=html5&clientVersion=500&distId=&facilitys=&gatesign="
              "&gatets=1793452609797&guestNum=&huXing=&keyword=&latitude=&leaseType="
              "&length=10&locId=&locLatitude=&locLongitude=&locName=&localSelected="
              "&lodgeUnitTags=&longitude=&maxPrice=&minPrice=&nation=0&offset=0"
              "&orderBy=recommend&radius=5&role=xzfk&roottype=&sessId=&ticket="
              "&timezone=%2B08:00&userId=&wttXMuWwbC=&xzToken=",
     "expected": "bbcddbf73477c3e35106054c8b129e5551e4776e"},
]


def main() -> None:
    passed = 0
    for case in SAMPLE_CASES:
        params = dict(parse_qsl(case["query"], keep_blank_values=True))
        got = sign(case["url"], params, case["placeholder"])
        ok = got == case["expected"]
        passed += ok
        print("[%s] %-34s %s" % ("PASS" if ok else "FAIL", case["name"], got))
        if not ok:
            print("       期望: %s" % case["expected"])

    # 附加: sign_url 回填后 query 里必须出现同一个签名
    case = SAMPLE_CASES[2]
    params = dict(parse_qsl(case["query"], keep_blank_values=True))
    qs, sig = sign_url(case["url"], params, case["placeholder"])
    ok = ("gatesign=" + sig) in qs and sig == case["expected"]
    passed += ok
    print("[%s] sign_url 回填" % ("PASS" if ok else "FAIL"))

    total = len(SAMPLE_CASES) + 1
    print("\n%d/%d 通过" % (passed, total))
    if passed != total:
        raise SystemExit(1)


# ---------------------------------------------------------------- 可选: 真实请求
# 签名校验状态（2026-10-31 实测）: 网关对 gatesign 目前「收但不硬校验」——
#   同一接口删掉 gatesign 照样 200，改错也只影响缓存命中。算法仍按真值复刻，
#   留作接口收紧后的即用件。真实请求用 sign_url() 拼 query 即可。

if __name__ == "__main__":
    main()
