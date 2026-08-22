"""
荔枝网 gdtv.cn (广东广播电视台) — WASM API 认证签名: 扣 webpack chunk + 5 补丁补环境

用法:
    python main.py            # 结构/确定性/参与项验证 (需 node, 无网络)
    python main.py --live     # 追加真实请求验证 (需网络)

原理 (vendor_w.js 698KB = webpack chunk 5, 内含 base64 内嵌 512KB WASM):
    签名链: S() (client.js) -> m() (chunk-libs.js) -> B.a() (module 266, Rust wasm-bindgen)
    输入:   B.a(METHOD, FULL_URL, deviceId, "WEB_PC", "", undefined)
    输出:   6 个 headers:
        content-type: application/json
        x-itouchtv-ca-timestamp: 13 位毫秒时间戳
        x-itouchtv-ca-signature: base64 (32 字节)
        x-itouchtv-ca-key:       固定常量 89541943007407288657755311868534
        x-itouchtv-client:       WEB_PC (平台参数回显)
        x-itouchtv-device-id:    设备 ID 回显
    5 个关键补丁 (signer.js):
        delete globalThis.global  <- WASM 检测 Node 的关键
        Window = function Window(){}
        Location.prototype = {href, origin, host, ...}
        document = { location }
        B.a 参数格式 (method + fullUrl, 不是 apiPath + body)
    验证结论 (固定时间戳实验):
        - URL 参与签名, method 参与签名
        - deviceId 不参与签名 (仅 header 回显)
        - 签名含时区偏移 (verify_fixed.js 固定 UTC+8 保证跨机器一致)

样例来源: 固定时间戳期望值 = verify_fixed.js 确定性输出 (2026-08-19 捕获);
          案例 1 与该时间戳下的真实 cli.js 运行逐位一致 (真实抓包复现).
"""

import base64
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request

DIR = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(DIR, "env_patch", "cli.js")
FIXED_CLI = os.path.join(DIR, "env_patch", "verify_fixed.js")

CA_KEY = "89541943007407288657755311868534"
DEFAULT_DEVICE = "WEB_nodejs_00000000-0000-0000-0000-000000000001"
HEADER_KEYS = {"content-type", "x-itouchtv-ca-timestamp", "x-itouchtv-ca-signature",
               "x-itouchtv-ca-key", "x-itouchtv-client", "x-itouchtv-device-id"}

# (method, url, deviceId, 固定时间戳期望签名) — verify_fixed.js 确定性输出
# 案例 1 与真实 cli.js (时间戳 1787153907256) 输出逐位一致 (2026-08-19)
FIXED_TS = 1787153907256
SAMPLE_CASES = [
    ("GET", "https://gdtv-api.gdtv.cn/api/v1/seoConfig", DEFAULT_DEVICE,
     "60d/Glg/VwPL9PCVYhIRgoJVgJpqWjkrepfedVPk+FI="),
    ("GET", "https://gdtv-api.gdtv.cn/api/channel/v1/news?channelId=117&pageSize=5",
     DEFAULT_DEVICE, "jITwRysCOmFDmBl9h0PDpEh5k7vlmADCDfbTivbC4aA="),
    ("POST", "https://gdtv-api.gdtv.cn/api/v1/seoConfig", DEFAULT_DEVICE,
     "a7Eq2YbLe5S0reS6xpkTQdSwGNGsBWlJ56I2xCHtmFk="),
]


def run_node(cli: str, *args) -> dict:
    """node <cli> <args...> -> headers dict (utf-8, 防 GBK 解码崩)"""
    out = subprocess.run(["node", cli, *map(str, args)],
                         capture_output=True, text=True, encoding="utf-8",
                         errors="replace", check=True)
    return json.loads(out.stdout.strip().splitlines()[0])


def sign_fixed(method: str, url: str, device_id: str = DEFAULT_DEVICE) -> dict:
    """固定时间戳签名 (verify_fixed.js, 排除时间变量做参与项分析)"""
    return run_node(FIXED_CLI, method, url, device_id)


def sign_random(method: str, url: str, device_id: str = DEFAULT_DEVICE) -> dict:
    """真实签名 (cli.js, 时间戳取当前时间)"""
    return run_node(CLI, method, url, device_id)


def check_signature_shape(h: dict) -> bool:
    """6 headers 结构: 键集合 + ca-key 常量 + client 回显 + 签名 32B base64 + 时间戳格式"""
    try:
        sig = base64.b64decode(h["x-itouchtv-ca-signature"], validate=True)
        ok = (set(h.keys()) == HEADER_KEYS and h["x-itouchtv-ca-key"] == CA_KEY
              and h["x-itouchtv-client"] == "WEB_PC"
              and len(sig) == 32
              and h["x-itouchtv-ca-timestamp"].isdigit()
              and len(h["x-itouchtv-ca-timestamp"]) == 13)
    except (KeyError, ValueError):
        return False
    return ok


def live_request() -> None:
    """真实请求: GET /api/v1/seoConfig -> 200 (原项目 env_patch 2026-06-21 实测 4/4)"""
    url = "https://gdtv-api.gdtv.cn/api/v1/seoConfig"
    h = sign_random("GET", url)
    h["User-Agent"] = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36")
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = resp.read().decode("utf-8")
    return resp.status, data


def main() -> None:
    if shutil.which("node") is None:
        print("FAIL: node.js required (WASM module cannot run in pure Python)")
        raise SystemExit(1)

    passed, total = 0, 0

    def check(ok: bool, label: str, detail: str = "") -> None:
        nonlocal passed, total
        total += 1
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label} {detail}")

    # 1. vendor_w.js 完整性 (webpack chunk 5)
    vendor = os.path.join(DIR, "vendor_w.js")
    check(os.path.isfile(vendor) and os.path.getsize(vendor) == 698165,
          "vendor_w.js intact", f"({os.path.getsize(vendor)} bytes)")

    # 2. 内嵌 base64 WASM 可提取 (512KB 解码)
    src = open(vendor, encoding="utf-8").read()
    m = re.search(r"data:application/wasm;base64,([A-Za-z0-9+/=]+)", src)
    wasm_bytes = base64.b64decode(m.group(1)) if m else b""
    check(m is not None and len(wasm_bytes) == 511963
          and wasm_bytes[:4] == b"\x00asm",
          "embedded wasm extractable", f"({len(wasm_bytes)} bytes)")

    # 3. signer.js 5 个关键补丁 (源码级检查)
    signer_src = open(os.path.join(DIR, "env_patch", "signer.js"), encoding="utf-8").read()
    patches = ["delete globalThis.global", "Window = function Window",
               "Location.prototype", "document = { location", "initSync"]
    check(all(p in signer_src for p in patches), "5 patches in signer.js",
          f"({sum(p in signer_src for p in patches)}/5)")

    # 4. 固定时间戳样例期望值 ×3 (案例 1 与真实抓包逐位一致)
    for method, url, dev, expect in SAMPLE_CASES:
        h = sign_fixed(method, url, dev)
        got = h.get("x-itouchtv-ca-signature")
        check(got == expect and check_signature_shape(h),
              f"fixed-ts sample {method} {url.split('/')[-1]}", f"({got})")

    # 5. 确定性: 相同输入两次运行一致
    a = sign_fixed("GET", "https://gdtv-api.gdtv.cn/api/v1/seoConfig")
    b = sign_fixed("GET", "https://gdtv-api.gdtv.cn/api/v1/seoConfig")
    check(a == b, "fixed-ts determinism", f"({a['x-itouchtv-ca-signature']})")

    # 6. deviceId 不参与签名 (仅 header 回显)
    c = sign_fixed("GET", "https://gdtv-api.gdtv.cn/api/v1/seoConfig", "WEB_other-device")
    check(c["x-itouchtv-ca-signature"] == a["x-itouchtv-ca-signature"]
          and c["x-itouchtv-device-id"] == "WEB_other-device",
          "deviceId not signed (header echo only)", "")

    # 7. 随机签名: 时间戳贴近当前时间 (13 位毫秒)
    r = sign_random("GET", "https://gdtv-api.gdtv.cn/api/v1/seoConfig")
    ts = int(r["x-itouchtv-ca-timestamp"])
    check(abs(ts - int(time.time() * 1000)) < 5 * 60 * 1000,
          "live timestamp sanity", f"(now-ts={abs(ts - int(time.time() * 1000))}ms)")

    # 8. 非确定性: 随机时间戳两次运行不同
    r2 = sign_random("GET", "https://gdtv-api.gdtv.cn/api/v1/seoConfig")
    check(r["x-itouchtv-ca-signature"] != r2["x-itouchtv-ca-signature"],
          "random-ts non-determinism", "")

    # 9. 签名格式: 标准 base64, 解码 32 字节
    check(check_signature_shape(r), "signature shape (b64 -> 32B, 6 headers)",
          f"(sig len {len(r['x-itouchtv-ca-signature'])})")

    # 10. 真实请求 (可选)
    if "--live" in sys.argv:
        status, data = live_request()
        ok = status == 200 and data.strip().startswith("{")
        check(ok, "live request", f"(HTTP {status}, body {len(data)} bytes)")
    else:
        print("[SKIP] --live real request (add --live, needs network)")

    print(f"\n{passed}/{total} passed")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
