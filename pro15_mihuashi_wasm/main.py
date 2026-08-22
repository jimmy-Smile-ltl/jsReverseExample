"""
米画师 (www.mihuashi.com) — WASM 签名: 8 补丁补环境 + Rust wasm-bindgen 模块

用法:
    python main.py            # 结构/确定性/边界验证 (需 node, 无网络)
    python main.py --live     # 追加真实请求验证 (需网络)

原理 (mhs_fe_sign_bg.wasm 64KB, Rust + wasm-bindgen):
    页面拦截器 http.B6ZEV3BE.js 对每个请求:
        1. ts = Math.floor(Date.now() / 1000)
        2. u  = encodeURI(e.url)        # 只签 PATH! 带 query 会被 403
        3. M-S = Signtool.sign(u, ts)   # WASM 内: 指纹(favicon+UA) + 32B 随机 nonce
        4. headers: M-S / M-T / Web-Version: frontend
    关键点:
        - 服务端校验 User-Agent == 签名内嵌的 navigator.userAgent (run_sign.js 第 86 行)
        - 非确定性 (随机 nonce); 固定 0x42 nonce 时浏览器 == Node 字节级一致
        - signtool_new 间歇失败 (~30%), run_sign.js 内置 30 次重试
        - 签名长度与 PATH 长度正相关: 28 字符 PATH -> 100 字符签名
        - 输出 charset: base64url 变体 (`_` 与 `/` 共存, 无 `=` 填充)

样例来源: 固定 nonce (全 0x42) 期望值 = 原项目 2026-06-21 浏览器==Node 字节一致验证,
          2026-08-19 用 verify_fixed.js 从本目录 Node 运行器捕获 (与浏览器逐位一致).
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request

DIR = os.path.dirname(os.path.abspath(__file__))

# 签名内嵌的 navigator.userAgent (run_sign.js 第 86 行) — 服务端与 HTTP header 比对!
UA_EXPECT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36")

# (PATH, 时间戳, 固定 nonce 期望签名, 期望长度) — 取自原项目 2026-06-21 浏览器实测对比链路;
# 长度与 PATH 长度正相关: 28 字符 PATH -> 100, 18 -> 92, 23 -> 96
SAMPLE_CASES = [
    ("/api/v1/artworks/search", 1782048550,
     "NQu2qdIWBMsi_42RF1iUmV0btJVVthTQv1mJMdTLjh2a0IDM2MDN3YTOx0mba9WR4gTUt1UK7ATdspnb4YlVSd2cNVlNzRERVxDP", 100),
    ("/api/v1/artworks", 1782048550,
     "NQu2qdIWBMsi__gUmV0btJVVthTQv1WKt1ULjh2a0IDM2ITO5MjNx0SRH5mJRhDO7ATdspnb4YlVSd2cNVlNzRERVxDP", 92),
    ("/api/v1/artworks/hot", 1782048550,
     "NQu2qdIWBMsi_UULSZWRv1mUV1GOB9WbmEVbtMGarRjMwYzM2EDOyUzRu12NtYGO40UK7ATdspnb4YlVSd2cNVlNzRERVxDP", 96),
]

BASE64URL_VARIANT = re.compile(r"^[A-Za-z0-9_/]+$")


def run_node(cli: str, *args) -> str:
    """node <cli> <args...> -> stdout (utf-8, 防 GBK 解码崩)"""
    out = subprocess.run(["node", os.path.join(DIR, cli), *map(str, args)],
                         capture_output=True, text=True, encoding="utf-8",
                         errors="replace", check=True)
    return out.stdout.strip().splitlines()[0]


def node_sign(url_path: str, ts: int) -> str:
    """随机 nonce 签名 (对应生产路径 sign.js)"""
    return json.loads(run_node("sign.js", url_path, f"--ts={ts}"))["signature"]


def node_sign_fixed(url_path: str, ts: int) -> str:
    """固定 0x42 nonce 签名 (verify_fixed.js, 仅算法验证 — 低熵会被服务端拒绝)"""
    return json.loads(run_node("verify_fixed.js", url_path, str(ts)))["signature"]


def extract_path(full_url: str) -> str:
    """只取 URL PATH — 对应拦截器 encodeURI(e.url) 的语义 (query 不参与签名)"""
    return urllib.parse.urlparse(full_url).path


def sign_headers(full_url: str, ts: int = None, max_retries: int = 5) -> dict:
    """生产助手: PATH 签名 + 必需 headers (signtool_new 间歇失败, 需重试)

    signtool_new 约 30% 概率产生长度正确但内容无效的签名, 重试直到 len==100.
    """
    if ts is None:
        ts = int(time.time())
    path = extract_path(full_url)
    for _ in range(max_retries):
        sig = node_sign(path, ts)
        if len(sig) == 100:
            return {"M-S": sig, "M-T": str(ts), "Web-Version": "frontend",
                    "User-Agent": UA_EXPECT,
                    "Authorization": "Bearer null",
                    "Accept": "application/json, text/plain, */*"}
    raise RuntimeError(f"sign failed after {max_retries} retries: {full_url}")


def live_request() -> None:
    """真实请求验证: GET /api/v1/artworks/search -> 200 (原项目 2026-06-21 实测 6/6)"""
    full = "https://www.mihuashi.com/api/v1/artworks/search?page=1&type=recent"
    headers = sign_headers(full)
    req = urllib.request.Request(full, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
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

    # 1. WASM 模块完整性
    wasm = os.path.join(DIR, "mhs_fe_sign_bg.wasm")
    check(os.path.isfile(wasm) and os.path.getsize(wasm) == 64979,
          "wasm module intact", f"({os.path.getsize(wasm)} bytes)")

    # 2. UA 补丁与签名内嵌值一致 (run_sign.js 第 86 行)
    src = open(os.path.join(DIR, "run_sign.js"), encoding="utf-8").read()
    m = re.search(r"userAgent:\s*'([^']+)'", src)
    check(m and m.group(1) == UA_EXPECT, "UA patch source", f"({m.group(1)[:36]}...)")

    # 3. 固定 nonce 样例期望值 ×3 (原项目浏览器==Node 字节一致的延伸)
    for path, ts, expect, elen in SAMPLE_CASES:
        got = node_sign_fixed(path, ts)
        check(got == expect and len(got) == elen, f"fixed-nonce sample {path}",
              f"(len {len(got)}, expect {elen})")

    # 4. 确定性: 固定 nonce 两次运行字节一致
    a = node_sign_fixed("/api/v1/artworks/search", 1782048550)
    b = node_sign_fixed("/api/v1/artworks/search", 1782048550)
    check(a == b, "fixed-nonce determinism", f"({a[:20]}...)")

    # 5. 非确定性: 随机 nonce 相同输入不同输出
    c = node_sign("/api/v1/artworks/search", 1782048550)
    d = node_sign("/api/v1/artworks/search", 1782048550)
    check(c != d and len(c) == 100 and len(d) == 100,
          "random nonce non-determinism", f"(len {len(c)}/{len(d)})")

    # 6. charset: base64url 变体 (`_` 与 `/`, 无 `=`)
    check(BASE64URL_VARIANT.match(c) is not None, "signature charset",
          f"(no padding, len%4={len(c) % 4})")

    # 7. 覆盖边界: 签名只签 PATH, 带 query -> 124 字符 -> 生产环境 403
    q = node_sign("/api/v1/artworks/search?page=1&type=recent", 1782048550)
    check(len(q) == 124 and q != c, "PATH-only coverage", f"(query -> len {len(q)})")

    # 8. extract_path: 完整 URL -> PATH
    check(extract_path("https://www.mihuashi.com/api/v1/artworks/search"
                       "?page=1&type=recent") == "/api/v1/artworks/search",
          "extract_path helper", "")

    # 9. sign_headers 组装 (含重试)
    h = sign_headers("https://www.mihuashi.com/api/v1/artworks/search?page=1",
                     ts=1782048550)
    check(h["M-T"] == "1782048550" and h["Web-Version"] == "frontend"
          and len(h["M-S"]) == 100 and h["User-Agent"] == UA_EXPECT,
          "sign_headers assembly", f"(M-S len {len(h['M-S'])})")

    # 10. 真实请求 (可选)
    if "--live" in sys.argv:
        status, data = live_request()
        check(status == 200 and "total_pages" in data,
              "live request", f"(HTTP {status}, total_pages={data.get('total_pages')})")
    else:
        print("[SKIP] --live real request (add --live, needs network)")

    print(f"\n{passed}/{total} passed")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
