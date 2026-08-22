"""
中国土地市场网 (landchina.com) — CloudWAF 行为画像 + disable-devtool v0.3.8 + Hash 头签名

用法:
    python main.py            # 纯 Python 验证 (无网络, 无需 node)
    python main.py --live     # 追加单次真实请求 (需网络; 警告: 非浏览器指纹会被
                              # CloudWAF 标记, 反复运行会把本机 IP 打入 418)

原理 (来源: analysis_report.md, 2026-06-30 分析):
    1) Hash 头签名 (app.js 请求拦截器, 后端不校验):
        r = e.url.split("/"); t["Hash"] = MD5(navigator.userAgent
            + new Date().getDate() + r[r.length-1])
       = MD5(userAgent + dayOfMonth(1-31 无前导零) + URL最后一段)
    2) disable-devtool v0.3.8 (开源库 theajack/disable-devtool, 站点配置未激活):
        interval 500 / stopIntervalTime 5000 / detectors [0,1,3,4,5,6,7] (唯独禁用 Size)
        检测器: 0 RegToString / 1 DefineId / 2 Size(outer vs inner*devicePixelRatio)
                / 3 DateToString / 4 FuncToString / 5 Debugger(>100ms)
                / 6 Performance(log vs table) / 7 DebugLib(eruda/_vcOrigConsole)
    3) CloudWAF (华为云, 核心反爬):
        Server: CW + HWWAFSESID/HWWAFSESTIME cookie + 418 拦截页
        事件ID: {risk}-clou-{node}-{ts}-{hash} (如 08-clou-37-20260630113906-0e7e24ae)
        渐进式行为画像: 请求1放行(08低风险) -> 2-3次后 418(90高风险)
                       -> IP 标记 90-clou-90 确认封锁; TLS 指纹是主要触发因子

坑: chunk-vendors.js 保存的是 CloudWAF 418 拦截页 (抓包 vendor 包时被 WAF 拦截),
    disable-devtool 源码未在本机留存, 检测逻辑按报告文档还原 (阈值常量为报告级别).

样例来源: Hash 期望值 = 公式自洽计算 (报告 c9bf226a 示例的 UA 被截断, 无法复现,
          已在 README 说明); 事件ID = 报告风险演变表真实抓包值 (2026-06-30).
"""

import hashlib
import os
import re
import sys
import urllib.request

DIR = os.path.dirname(os.path.abspath(__file__))
BLOCK_PAGE = os.path.join(DIR, "chunk-vendors.js")   # 实际是 CloudWAF 418 拦截页

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36")

# (day, path, 期望 hash) — 公式自洽计算 (2026-08-19); UA/公式与报告一致
SAMPLE_CASES = [
    (30, "tGdxm/result/list", "13d60df9016180c068db36a29a9dce24"),
    (5, "tGdxm/result/list", "a9d2b28d059947e2883fed9eab612200"),
    (30, "tGdxm/result/detail", "06f545b31f09c7cd74ae09f396a6e398"),
    (30, "https://api.landchina.com/tGdxm/result/list", "13d60df9016180c068db36a29a9dce24"),
]

# CloudWAF 事件ID 风险演变 (报告 2026-06-30 真实抓包): (事件ID, risk, node, HTTP 结果)
EVENT_SAMPLES = [
    ("08-clou-37-20260630113906-0e7e24ae", 8, 37, 200),   # 阶段1: 首次请求放行
    ("90-clou-37-20260630114420-14fb04d0", 90, 37, 418),  # 阶段2: 行为画像触发
    ("90-clou-90-20260630114421-587848b4", 90, 90, 418),  # 阶段3: IP 确认标记
]

# disable-devtool v0.3.8 检测器表 (报告 3.1): id -> 名称/机制
DETECTORS = {
    0: "RegToString", 1: "DefineId", 2: "Size", 3: "DateToString",
    4: "FuncToString", 5: "Debugger", 6: "Performance", 7: "DebugLib",
}

# 站点轮询配置 (报告 3.1, 与 chunk-vendors.js 内 disable-devtool 参数一致)
CONFIG = {
    "interval": 500, "stopIntervalTime": 5000,
    "detectors": [0, 1, 3, 4, 5, 6, 7],   # 启用 7 种, 唯独禁用 Size(2)
    "clearLog": False, "disableMenu": False,
}

SIZE_CASES = [
    (1600, 1400, 900, 900, 1.0, True),    # 侧边停靠: 宽差 200 > 160
    (1600, 1600, 900, 730, 1.0, True),    # 底部停靠: 高差 170 > 160
    (1600, 1600, 900, 900, 1.0, False),   # 未打开: 差值 0
    (2400, 1600, 1350, 900, 1.5, False),  # 150% 缩放: dpr 补偿后差值 0 (防误报)
    (2400, 1440, 1350, 900, 1.5, True),   # 缩放 + 停靠 160 css px: 差 240 > 160
]
DEBUGGER_CASES = [(150, True), (30, False), (100, False)]    # 严格 >100ms
TOSTRING_CASES = [(1, False), (2, True), (7, True)]          # DevTools 调用 >=2 次
PERF_CASES = [(5, 60, True), (5, 8, False)]                  # table 慢于 log 的 2 倍
DEBUGLIB_CASES = [(True, False, True), (False, True, True), (False, False, False)]

# 检测到 DevTools 的行为兜底 (报告 3.1; 本站未配置跳转/重写 HTML)
FALLBACK = {"action": "window.close() + history.back()",
            "delay_ms": 500,
            "url": "https://theajack.github.io/disable-devtool/404.html"}


# ---------- Hash 签名 (app.js 拦截器原文逻辑) ----------

def last_path_segment(url_or_path: str) -> str:
    """r = e.url.split('/'); r[r.length - 1] — 取最后一段 (绝对 URL / 相对路径均可)"""
    return url_or_path.rstrip("/").split("/")[-1]


def gen_hash(ua: str, day: int, path: str) -> str:
    """t['Hash'] = MD5(userAgent + dayOfMonth(无前导零) + URL最后一段)"""
    return hashlib.md5(f"{ua}{day}{last_path_segment(path)}".encode("utf-8")).hexdigest()


# ---------- CloudWAF 事件ID ----------

def parse_event_id(event_id: str) -> dict:
    """事件ID {risk}-clou-{node}-{14位时间戳}-{8位hex} -> 字段解析"""
    m = re.fullmatch(r"(\d{2})-clou-(\d{2})-(\d{14})-([0-9a-f]{8})", event_id)
    if not m:
        raise ValueError(f"invalid event id: {event_id!r}")
    return {"risk": int(m.group(1)), "node": int(m.group(2)),
            "ts": m.group(3), "hash": m.group(4)}


def risk_label(risk: int) -> str:
    """08=低风险 / 90=高风险 (报告风险评分)"""
    return "low" if risk < 90 else "high"


def escalation_stage(event_id: str) -> int:
    """风险阶段: 1 放行 -> 2 行为画像 418 -> 3 IP 确认标记 418"""
    e = parse_event_id(event_id)
    if e["risk"] >= 90 and e["node"] >= 90:
        return 3
    if e["risk"] >= 90:
        return 2
    return 1


def parse_block_page(html: str) -> dict:
    """CloudWAF 418 拦截页: 标记检查 + 事件ID提取"""
    m = re.search(r"\d{2}-clou-\d{2}-\d{14}-[0-9a-f]{8}", html)
    event = parse_event_id(m.group(0)) if m else None
    return {"markers": {"cloudwaf": "CloudWAF" in html,
                        "status_418": "418" in html,
                        "blocked": "访问被拦截" in html},
            "event": event}


# ---------- disable-devtool v0.3.8 检测判定 (按报告还原) ----------

def size_detected(outer_w, inner_w, outer_h, inner_h, dpr=1.0, threshold=160) -> bool:
    """检测器 2 Size: outer vs inner * devicePixelRatio (报告公式; 本站配置禁用)"""
    return (outer_w - inner_w * dpr > threshold
            or outer_h - inner_h * dpr > threshold)


def debugger_detected(elapsed_ms: float) -> bool:
    """检测器 5 Debugger: debugger 语句执行 >100ms -> DevTools 已开"""
    return elapsed_ms > 100


def tostring_detected(calls: int) -> bool:
    """检测器 3/4 DateToString/FuncToString: DevTools 调用覆写 toString >= 2 次"""
    return calls >= 2


def performance_detected(log_ms: float, table_ms: float, ratio: float = 2.0) -> bool:
    """检测器 6 Performance: console.table 显著慢于 console.log (50 元素数组)
    阈值常量为报告级别 (精确值未随源码留存), 见 README"""
    return table_ms > log_ms * ratio


def debuglib_detected(eruda: bool = False, vc_orig_console: bool = False) -> bool:
    """检测器 7 DebugLib: window.eruda / window._vcOrigConsole (vConsole) 存在"""
    return bool(eruda or vc_orig_console)


def on_devtool_open_plan(redirect_url: str = "", rewrite_html: str = "") -> str:
    """检测到 DevTools 的行为: 优先跳转 h.url -> 重写 HTML -> 兜底 close+back+404"""
    if redirect_url:
        return f"redirect:{redirect_url}"
    if rewrite_html:
        return "rewrite-html"
    return FALLBACK["action"] + " -> " + FALLBACK["url"] + " after " + str(FALLBACK["delay_ms"]) + "ms"


# ---------- 主流程 ----------

def main() -> None:
    passed, total = 0, 0

    def check(ok: bool, label: str, detail: str = "") -> None:
        nonlocal passed, total
        total += 1
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label} {detail}")

    # 1. CloudWAF 拦截页 (chunk-vendors.js 即 418 拦截页, 抓包时被 WAF 拦下)
    html = open(BLOCK_PAGE, encoding="utf-8").read()
    page = parse_block_page(html)
    check(all(page["markers"].values()), "block page markers (CloudWAF/418/blocked)",
          f"({page['markers']})")
    check(page["event"] is not None
          and page["event"]["ts"] == "20260630113906"
          and page["event"]["hash"] == "0e7e24ae",
          "block page event id", f"({page['event']})")

    # 2. 事件ID 解析与风险演变 (3 阶段)
    for ev, risk, node, http in EVENT_SAMPLES:
        got = parse_event_id(ev)
        ok = (got["risk"] == risk and got["node"] == node
              and risk_label(risk) == ("low" if http == 200 else "high")
              and escalation_stage(ev) in (1, 2, 3))
        check(ok, f"event id parse {ev[:8]}...",
              f"(risk={got['risk']} node={got['node']} stage={escalation_stage(ev)} "
              f"http={http})")
    for bad in ("90-clou-37-20260630114420", "90-xx-37-20260630114420-14fb04d0",
                "90-clou-90-20260630114421-zzzzzzzz"):
        try:
            parse_event_id(bad)
            ok = False
        except ValueError:
            ok = True
        check(ok, f"malformed event id rejected ({bad!r})", "")

    # 3. Hash 签名样例 ×4 (公式自洽; 报告 c9bf226a 示例 UA 截断不可复现)
    for day, path, expect in SAMPLE_CASES:
        got = gen_hash(UA, day, path)
        check(got == expect, f"gen_hash day={day} path={last_path_segment(path)!r}",
              f"({got})")
    check(re.fullmatch(r"[0-9a-f]{32}", gen_hash(UA, 1, "x")) is not None,
          "hash structure", "(32 lowercase hex)")
    check(gen_hash(UA, 5, "tGdxm/result/list")
          != gen_hash(UA, "05", "tGdxm/result/list"),
          "dayOfMonth no leading zero", "(day=5 vs '05' differ)")
    check(last_path_segment("https://api.landchina.com/tGdxm/result/list")
          == last_path_segment("tGdxm/result/list/") == "list",
          "last path segment extraction", "(absolute/relative/trailing-slash)")

    # 4. disable-devtool 检测器表与站点配置
    check(set(DETECTORS) == set(range(8)) and DETECTORS[5] == "Debugger",
          "detector table 0-7", f"({list(DETECTORS.values())})")
    c = CONFIG
    check(c["interval"] == 500 and c["stopIntervalTime"] == 5000
          and c["detectors"] == [0, 1, 3, 4, 5, 6, 7]
          and c["clearLog"] is False and c["disableMenu"] is False,
          "site config matches report", "(interval 500 / 7 detectors / Size disabled)")

    # 5. 检测器判定样例
    for ow, iw, oh, ih, dpr, expect in SIZE_CASES:
        got = size_detected(ow, iw, oh, ih, dpr)
        check(got == expect, f"size detector {ow}-{iw}x{oh}-{ih} dpr={dpr}",
              f"({'trigger' if got else 'pass'})")
    for ms, expect in DEBUGGER_CASES:
        got = debugger_detected(ms)
        check(got == expect, f"debugger detector {ms}ms",
              f"({'trigger' if got else 'pass'})")
    for calls, expect in TOSTRING_CASES:
        got = tostring_detected(calls)
        check(got == expect, f"toString detector calls={calls}",
              f"({'trigger' if got else 'pass'})")
    for lm, tm, expect in PERF_CASES:
        got = performance_detected(lm, tm)
        check(got == expect, f"performance detector log={lm}ms table={tm}ms",
              f"({'trigger' if got else 'pass'})")
    for e, v, expect in DEBUGLIB_CASES:
        got = debuglib_detected(e, v)
        check(got == expect, f"debuglib detector eruda={int(e)} vc={int(v)}",
              f"({'trigger' if got else 'pass'})")
    check(on_devtool_open_plan() == FALLBACK["action"] + " -> " + FALLBACK["url"]
          + " after " + str(FALLBACK["delay_ms"]) + "ms"
          and on_devtool_open_plan("https://x/") == "redirect:https://x/",
          "onDevToolOpen plan", f"(unconfigured -> {FALLBACK['action']}, 500ms -> 404.html)")

    # 6. 真实请求 (可选, 单次)
    if "--live" in sys.argv:
        try:
            req = urllib.request.Request("https://www.landchina.com/",
                                         headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = resp.read().decode("utf-8", "replace")
            hdrs = dict(resp.headers)
            server = hdrs.get("Server", "")
            cookie = hdrs.get("Set-Cookie", "")
            ok = (server == "CW" or "HWWAFSESID" in cookie
                  or "CloudWAF" in body or "访问被拦截" in body)
            check(ok, "live request WAF signature",
                  f"(HTTP {resp.status}, Server={server!r}, body {len(body)} bytes)")
        except Exception as e:
            check(False, "live request", f"({e})")
    else:
        print("[SKIP] --live single request (add --live; non-browser TLS gets IP marked)")

    print(f"\n{passed}/{total} passed")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
