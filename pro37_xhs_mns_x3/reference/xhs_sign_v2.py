# -*- coding: utf-8 -*-
"""参考脚本：X-S / X-S-Common 组装（2026-08-31 线上 200）

注意：完整运行依赖同目录的 Node 补环境产物与浏览器 cookie（仓库未随附）；
本文件仅保留请求头组装的公式与字段顺序，供学习参考。

小红书 X-S 签名 v2 (2026-08-30 逆向，webBuild 6.46.1 / language 4.4.3)

签名体系（对照 seccore_signv2 in vendor-dynamic.45753fe0.js）:
  X-S = "XYS_" + 自定义base64(JSON.stringify(S))   # 不做任何 URL 编码！(服务端严格校验编码形态)
  S = {
    x0: "4.4.3",            # languageVersion
    x1: "xhs-pc-web",
    x2: "Windows",
    x3: mnsv2(c, u, p),     # ← 唯一重难点: JSVMP 保护, 走浏览器 RPC
    x4: "object" | "",
    x5: md5(uri + body),    # 纯算 ✓
    x6: {appId: b64(sha1(md5bytes + S))},     # 可选（实测缺省也过）
    x7: {appId: b64(nonce4 + sha1(ssk+nonce) + ssk[32:])},  # 可选
  }
  c = uri + JSON.stringify(body), u = md5(c), p = md5(uri)

实测结论 (2026-08-30):
  - X-S 是唯一硬门槛; X-S-Common 校验松 (b1/x9 可省); x-rap-param/xy-direction 无需
  - x6/x7 缺省可通过; 若要生成需 localStorage.webSsk (X25519 交换自 as.xiaohongshu.com/api/sec/v1/shield/webprofile)
  - X-S 编码必须是 JSON.stringify 原样 → 自定义 base64, 不能 URL 编码 (quote 会导致 406!)
  - cookie 中 websectiga/sec_poison_id/ets/loadts 新旧均可

依赖: 本地浏览器 RPC 服务 (rpc_server.py, 127.0.0.1:8899) 提供 /mns 生成 x3
"""
import base64
import hashlib

# 归档结构: 纯算法模块在 ../01-纯算法, 加入搜索路径
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '01-纯算法'))
import json
import random
import struct
import time
import urllib.request

CUSTOM_B64 = 'ZmserbBoHQtNP+wOcza/LpngG8yJq42KWYj0DSfdikx3VT16IlUAFM97hECvuRX5'
STD_B64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
_B64_TRANS = str.maketrans(STD_B64, CUSTOM_B64)

LANGUAGE_VERSION = '4.4.3'
ARTIFACT_VERSION = '6.46.1'
APP_ID = 'xhs-pc-web'
OS_SYSTEM = 'Windows'

RPC_URL = 'http://127.0.0.1:8899'
X3_REPLAY_FALLBACK = None  # 可填入一个已抓取的 mns0301 x3 作为兜底


def custom_b64encode(b: bytes) -> str:
    return base64.b64encode(b).decode().translate(_B64_TRANS)

# ---- x3 后端: 默认 Node 补环境 (无浏览器/无登录/无cookie), 失败回退 RPC ----
_NODE_PROC = None  # 持久 Node 进程 (stdin JSON 行协议)


def _get_node_proc():
    global _NODE_PROC
    import os
    import subprocess
    import threading
    if _NODE_PROC is not None and _NODE_PROC.poll() is None:
        return _NODE_PROC
    base = os.path.dirname(os.path.abspath(__file__))
    _NODE_PROC = subprocess.Popen(
        ['node', os.path.join(base, 'node_x3_server.js')],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=base, bufsize=1, text=True)
    # 等 READY
    ready = threading.Event()

    def _watch():
        for line in _NODE_PROC.stderr:
            if 'NODE_READY' in line:
                ready.set()
                break
        # 继续读空 stderr 防止阻塞
        def _drain():
            for _ in _NODE_PROC.stderr:
                pass
        threading.Thread(target=_drain, daemon=True).start()
    threading.Thread(target=_watch, daemon=True).start()
    ready.wait(timeout=30)
    return _NODE_PROC


def node_x3(c: str, u: str, p: str) -> str:
    """Node 补环境生成 x3 (vm_code.js + jsdom, 无浏览器无登录)"""
    proc = _get_node_proc()
    import json as _json
    proc.stdin.write(_json.dumps({'c': c, 'u': u, 'p': p}) + '\n')
    proc.stdin.flush()
    line = proc.stdout.readline()
    if not line:
        raise RuntimeError('Node x3 服务无响应')
    r = _json.loads(line)
    if not r.get('ok'):
        raise RuntimeError(f"Node x3 失败: {r.get('err')}")
    return r['v']


def rpc_mns(c: str, u: str, p: str) -> str:
    """通过浏览器 RPC 生成 x3 (备用后端)"""
    req = urllib.request.Request(
        RPC_URL + '/mns',
        data=json.dumps({'c': c, 'u': u, 'p': p}).encode(),
        headers={'content-type': 'application/json'})
    r = json.loads(urllib.request.urlopen(req, timeout=30).read())
    if not r.get('ok'):
        raise RuntimeError(f'RPC 失败: {r.get("err")}')
    return r['v']


def gen_x3(uri: str, body: dict) -> str:
    body_str = json.dumps(body, separators=(',', ':'), ensure_ascii=False)
    c = uri + body_str
    u = hashlib.md5(c.encode()).hexdigest()
    p = hashlib.md5(uri.encode()).hexdigest()
    if X3_REPLAY_FALLBACK:
        return X3_REPLAY_FALLBACK
    try:
        # 首选: 纯 Python 算法 (2026-08-31 攻克, 实测 200)
        from gen_x3_pure import gen_x3 as pure_x3
        return pure_x3(c, u, p)
    except Exception:
        pass
    try:
        return node_x3(c, u, p)
    except Exception:
        return rpc_mns(c, u, p)


def gen_x_s(uri: str, body: dict = None, x3: str = None) -> str:
    """生成 X-S 头 (含 x5; x6/x7 缺省 — 实测可通过)"""
    body_str = json.dumps(body, separators=(',', ':'), ensure_ascii=False) if body is not None else ''
    c = uri + body_str
    x5 = hashlib.md5(c.encode()).hexdigest()
    if x3 is None:
        x3 = gen_x3(uri, body) if body is not None else gen_x3(uri, {})
    S = {
        'x0': LANGUAGE_VERSION,
        'x1': APP_ID,
        'x2': OS_SYSTEM,
        'x3': x3,
        'x4': 'object' if body is not None else '',
        'x5': x5,
    }
    # 关键: 不做 URL 编码, 直接 JSON.stringify → 自定义 base64
    return 'XYS_' + custom_b64encode(json.dumps(S, separators=(',', ':')).encode())


def diy_mrc(text: str) -> int:
    """b1 的 CRC32 变体 (x9 字段)"""
    table = []
    for i in range(255, -1, -1):
        j = i
        for _ in range(8, 0, -1):
            j = ((j & 0xFFFFFFFF) >> 1) ^ 0xedb88320 if j & 1 else (j & 0xFFFFFFFF) >> 1
        table.insert(0, j & 0xFFFFFFFF)
    i = -1
    for ch in text:
        i = table[255 & i ^ ord(ch)] ^ ((i & 0xFFFFFFFF) >> 8)
    return -1 ^ i ^ 0xedb88320


def gen_x_sc(a1: str, b1: str = None) -> str:
    """生成 X-S-Common (校验松, b1 可省)"""
    p = {
        's0': 5, 's1': '',
        'x0': '1', 'x1': LANGUAGE_VERSION, 'x2': OS_SYSTEM, 'x3': APP_ID,
        'x4': ARTIFACT_VERSION, 'x5': a1, 'x6': '', 'x7': '',
        'x8': b1 or None,
        'x9': int(diy_mrc(b1 or '')),
        'x10': 0, 'x11': 'normal',
    }
    return custom_b64encode(json.dumps(p, separators=(',', ':'), ensure_ascii=False).encode())


def gen_traces() -> dict:
    """X-B3-Traceid / X-T / X-Xray-Traceid"""
    import math
    seq = math.floor(random.random() * (1 << 23))
    part1 = hex((int(time.time() * 1000) << 23) | seq)[2:].zfill(16)
    long_val = (random.getrandbits(32) << 32) | random.getrandbits(32)
    part2 = hex(long_val)[2:].zfill(16)
    return {
        'X-B3-Traceid': ''.join(random.choices('abcdef0123456789', k=16)),
        'X-T': str(int(time.time() * 1000)),
        'X-Xray-Traceid': part1 + part2,
    }


def gen_xhs_headers(uri: str, body: dict = None, a1: str = '', b1: str = None, x3: str = None) -> dict:
    """一站式生成全部签名头"""
    headers = {
        'X-S': gen_x_s(uri, body, x3=x3),
        'X-S-Common': gen_x_sc(a1, b1),
    }
    headers.update(gen_traces())
    return headers
