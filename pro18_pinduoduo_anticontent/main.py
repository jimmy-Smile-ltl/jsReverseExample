# -*- coding: utf-8 -*-
"""
拼多多 (pinduoduo.com) anti_content 纯算法实现（标准库，零 Node 依赖）

真实流水线（2026-08-29 完整还原，推翻早期“RC4”误判）:

    22 个 collector 采集环境 → 自定义二进制序列化 (~340B)
    → zlib deflate (level 6，与 pako 逐字节一致，头 78 9C)
    → 追加 4B build CRC（crc32(Wt 源码 + ue 源码)，每 build 恒定）
    → budget 扰码 base64（每个 6bit 索引按随机 v 平移，v 由末尾 marker 泄露）
    → "0aq" 前缀，总长 372~378 字符

早期把该层误判为 RC4：直接按标准 base64 解会得到 D1 AA 开头的“密文”，
实际是未反扰码的假象。扰码是可逆映射而非加密，熵来源仅一个 Math.random 值。

运行:
    py main.py           # 离线：序列化原语 + 编码器 roundtrip + 3 组确定性向量
    py main.py --node    # 追加：generator/ 原版引擎全链路 + 结构互证（需 node）
    py main.py --live    # 追加：纯算法生成 → 真实 API 请求（需网络）
"""

import json
import os
import random
import subprocess
import sys
import urllib.parse
import urllib.request
import zlib

DIR = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(DIR, "generator")

# ---------- 环境常量（与补环境 env.js 对齐，服务端已验证接受） ----------
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36")          # 111 bytes
HREF = "https://www.pinduoduo.com/home/girlclothes/"
REFERRER = "https://www.pinduoduo.com/"
SCREEN_W, SCREEN_H = 1920, 1040                                    # availWidth/availHeight
WT_FLAGS = 160000            # tag10: Wt() 18 项反自动化指纹打包（env.js 环境下恒定）
BROWSER_FLAGS = 0            # tag26: opera/ff/safari/ie/chrome 5 项标志
ET = bytes([0x23, 0x07, 0xED, 0x43])   # deflate 尾部: crc32(Wt源码+ue源码)，每 build 恒定
# tag7 尾部 CRC: crc32(locationInfo collector 的 init/packN 方法源码)，每 build 恒定
TAG7_CRC = bytes([0xB2, 0x6E, 0x02, 0x69])

ALPHABET = "9240gsB6PftGXnlQTw_pdvz7EekDmuAWCVZ5UF-MSK1IHOchoaxqYyj8Jb3LrNiR"
NANO_CHARSET = "_~varfunctio0125634789bdegjhklmpqswxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


# ---------- 1. 序列化原语（fbeZ 模块 3：ek / va / nc / sc） ----------

def va(n: int) -> bytes:
    """LEB128 小端 varint（7bit/组，高位=续位）。"""
    n = abs(int(n))
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n == 0:
            out.append(b)
            break
        out.append(b | 0x80)
    return bytes(out)


def nc(n: int) -> bytes:
    """数字 → 大端最小字节（abs 的二进制补齐 8 位组）。"""
    n = abs(int(n))
    bits = bin(n)[2:]
    bits = bits.zfill(((len(bits) + 7) // 8) * 8)
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))


def sc(s: str) -> bytes:
    """字符串 → UTF-8 字节（无长度前缀）。"""
    return s.encode("utf-8")


def ek(tag: int, value) -> bytes:
    """元素: 1 字节 tag（tag<<3 | min(len,7)），len>=8 时跟 va 长度，然后数据。"""
    if isinstance(value, str):
        data = sc(value)
    elif isinstance(value, int):
        data = nc(value)
    else:
        data = bytes(value)
    u = len(data)
    head = bytearray([(tag << 3) | (u if 0 < u <= 7 else 0)])
    if u > 7:
        head += va(u)
    return bytes(head) + data


# ---------- 2. budget 扰码 base64（模块 3 encode，非加密） ----------

def _budget(t: int, v: int) -> int:
    if t == 64:
        return 64
    if t == 63:
        return v
    return t + 1 if t >= v else t


def encode(data: bytes, v: int) -> str:
    """标准 base64 语义 + 每 6bit 索引经 budget 平移；去 '=' 后追加 marker ALPH[v]。"""
    alph_pad = ALPHABET + "="   # 索引 64 = 填充字符
    out = []
    for i in range(0, len(data), 3):
        b0 = data[i]
        b1 = data[i + 1] if i + 1 < len(data) else None
        b2 = data[i + 2] if i + 2 < len(data) else None
        a = b0 >> 2
        ii = ((b0 & 3) << 4) | ((b1 or 0) >> 4)
        c = (((b1 or 0) & 15) << 2) | ((b2 or 0) >> 6)
        u = (b2 or 0) & 63
        if b1 is None:      # 1 字节余数 → 2 个填充
            c = u = 64
        elif b2 is None:    # 2 字节余数 → 1 个填充
            u = 64
        a = _budget(a, v)
        ii = _budget(ii, v)
        c = _budget(c, v)
        u = _budget(u, v)
        out.append(alph_pad[a])
        out.append(alph_pad[ii])
        out.append(alph_pad[c])
        out.append(alph_pad[u])
    return "".join(out).replace("=", "") + ALPHABET[v]


def decode_anti_content(anti: str) -> bytes:
    """逆向 budget 扰码，返回 deflate + ET 字节（用于结构验证）。"""
    body = anti[3:]
    v = ALPHABET.index(body[-1])
    body = body[:-1]
    indices = []
    for ch in body:
        y = ALPHABET.index(ch)
        if y == v:
            indices.append(63)
        elif y > v:
            indices.append(y - 1)
        else:
            indices.append(y)
    bits = "".join(format(x & 63, "06b") for x in indices)
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits) // 8 * 8, 8))


# ---------- 3. 字段构造 ----------

def _crc4(s: str) -> bytes:
    """pbc()：crc32 大端 4 字节（tag11 用）。"""
    return zlib.crc32(s.encode("utf-8")).to_bytes(4, "big")


def nano_fp(rng: random.Random, now_ms: int) -> str:
    """tag16/17 nano 指纹（模块14 g()）。

    特殊字母表、不做扰码的 base64(时间戳前10位 + 校验3位右补0) + '_' + 21 位随机串；
    校验 = sum(charCode(ts10 + '_' + rand21)) % 1000（JS pad helper 为右补 0）。
    """
    ts10 = str(now_ms)[:10]
    rand21 = "".join(rng.choice(NANO_CHARSET) for _ in range(21))
    d = sum(ord(ch) for ch in (ts10 + "_" + rand21)) % 1000
    f = str(d).ljust(3, "0")
    bits = "".join(format(b, "08b") for b in (ts10 + f).encode())
    bits += "0" * (-len(bits) % 6)
    b64 = "".join(ALPHABET[int(bits[i:i + 6], 2)] for i in range(0, len(bits), 6))
    return b64 + "_" + rand21


def build_payload(server_time: int, init_ms: int, now_ms: int, counter: int,
                  rng: random.Random) -> bytes:
    """21 字段 payload（空 cookie、无交互事件的干净环境）。"""
    buf = bytearray()

    # tag7 location: 0x38 + va(hrefLen) + href + va(0) + 源码 CRC
    href_b = HREF.encode()
    buf.append(0x38)
    buf += va(len(href_b))
    buf += href_b
    buf += va(0)
    buf += TAG7_CRC

    # tag8 screen: 0x40 + va(w) + va(h)
    buf.append(0x40)
    buf += va(SCREEN_W)
    buf += va(SCREEN_H)

    # tag9 device_id: (p1 + p2) 数值相加 + "-" + serverTime（和恰 16 位）
    p1 = int(rng.random() * (2 ** 52 + 1))
    p2 = int(rng.random() * (2 ** 30 + 1))
    buf += ek(9, "%d-%d" % (p1 + p2, server_time))

    # tag10 Wt 指纹: 0x50 + va(160000)
    buf.append(0x50)
    buf += va(WT_FLAGS)

    # tag11: 0x58 + crc4(href)
    buf.append(0x58)
    buf += _crc4(HREF)

    # tag12/13 DeviceOrientation/DeviceMotion 存在性: "n"
    buf += ek(12, "n")
    buf += ek(13, "n")

    # tag14: 距初始化的毫秒数
    buf += ek(14, now_ms - init_ms)

    # tag15 UA
    buf += ek(15, UA)

    # tag16/17 nano cookie/storage 指纹（模块14 g()）
    nfp = nano_fp(rng, now_ms)
    buf += ek(16, nfp)
    buf += ek(17, nfp)

    # tag18 referrer
    buf += ek(18, REFERRER)

    # tag19/20/23（cookie pdd_user_id/api_uid/pdd_vds）— 无 cookie 时缺席
    # tag21 请求计数器
    buf += ek(21, counter)

    # tag22 初始化时间戳（Date.now 毫秒）
    buf += ek(22, init_ms)

    # tag26 浏览器标志: 0xd0 + va(0)
    buf.append(0xD0)
    buf += va(BROWSER_FLAGS)

    # header: [03 01 00 00] + 2 字节 BE 长度
    n = len(buf)
    len_b = bytes([0, n]) if n <= 255 else n.to_bytes(2, "big")
    return b"\x03\x01\x00\x00" + len_b + bytes(buf)


# ---------- 4. 主入口 ----------

def generate_anti_content(server_time=None, rng=None, init_ms=None, now_ms=None,
                          counter=1) -> str:
    """生成 anti_content。

    参数留出注入点仅为可复现; 生产直接 generate_anti_content() 即可。
    """
    rng = rng or random
    if server_time is None:
        import time
        server_time = int(time.time())
    if init_ms is None:
        import time
        init_ms = int(time.time() * 1000)
    if now_ms is None:
        import time
        now_ms = int(time.time() * 1000)

    payload = build_payload(server_time, init_ms, now_ms, counter, rng)
    compressed = zlib.compress(payload, 6)          # level 6 = pako 默认
    data = compressed + ET                          # 4B build CRC
    v = rng.randint(0, 63)
    return "0aq" + encode(data, v)


# ---------- 5. 验证辅助 ----------

def check_anti_structure(anti: str) -> tuple:
    """解码 + 解压 + 字段断言，返回 (ok, detail)。"""
    if not anti.startswith("0aq"):
        return False, "(prefix)"
    try:
        raw = decode_anti_content(anti)
        payload = zlib.decompress(raw[:-4])
    except Exception as exc:                        # noqa: BLE001 - 校验用
        return False, "(%s)" % exc
    detail = "(%d chars, payload %dB, zlib %dB)" % (len(anti), len(payload), len(raw) - 4)
    ok = (raw[-4:] == ET
          and payload[:4] == b"\x03\x01\x00\x00"
          and int.from_bytes(payload[4:6], "big") == len(payload) - 6
          and HREF.encode() in payload and UA.encode() in payload
          and REFERRER.encode() in payload
          and TAG7_CRC in payload and _crc4(HREF) in payload
          and payload.endswith(b"\xd0" + va(BROWSER_FLAGS)))
    return ok, detail


def _read_va(data, pos):
    """读 LEB128 varint，返回 (value, next_pos)。"""
    n, shift = 0, 0
    while True:
        b = data[pos]
        pos += 1
        n |= (b & 0x7F) << shift
        if not b & 0x80:
            return n, pos
        shift += 7


def parse_device_id(payload: bytes) -> str:
    """按 tag7 -> tag8 -> tag9 顺序解析出 device_id（供格式断言）。"""
    pos = 6
    assert payload[pos] == 0x38
    pos += 1
    ln, pos = _read_va(payload, pos)
    pos += ln
    pl, pos = _read_va(payload, pos)
    pos += pl + 4
    assert payload[pos] == 0x40
    pos += 1
    _, pos = _read_va(payload, pos)
    _, pos = _read_va(payload, pos)
    assert payload[pos] == 0x48
    pos += 1
    ln, pos = _read_va(payload, pos)
    return payload[pos:pos + ln].decode()


# 确定性向量: (seed, server_time, init_ms, now_ms, counter, expected)
# 由经典纯算法（2026-08-29，线上 8/8）以同 seed/时间生成，逐字节对拍
SAMPLE_CASES = [
    (20260829, 1788020797, 1788020797000, 1788020797113, 1,
     "0aqAfxUeMwVEQ_JyXbKt_FKccG7GqNojqoPYgO1YTm5oApN7Q8XWnxdWCpXK1YFSQq_Unw5CEenAdqe0VJNgYVN1PJX0mJXpmycGdanp9JXUTxy0mycG9qX0XacYTXk6SsBw0LNC_ExGYloOG95JYAWtUXSfj6CvXi9T_XmkguRADB47b54KEBAVDd4dX0XxsIZaOxgdNBxK49SnpajqphYwnWd8sYQ8gx2aiOUxnu6wqgSXYcvapyjlpcCdNg3KaUFnFXp4Yy0gsTPpFxGGXIgkMST54UPimKxOtqPXXZnq5OXOmVf5dilqYnfGgI840EhcgxXONVomqLlmlFVzhdgtuYZcffxBRX4oaViUaOX90w1DDXU2Rj0W"),
    (20260830, 1788050000, 1788050000000, 1788050000237, 5,
     "0aqWtxUkM_VeTpYynbKGpFKccXEXqNojqofYgO1Ywu5oWdNET8nBlxvBCdnK1YFSTqpUl_5CeklWvqk0VJNgYVN1fxnXnqnXfacd9aOY4xnYPwlYpyO0galV44Vb_sS_Qd088upNYXY4ci73ToMz8EM34dIMRKkG65g9LJfXqi7N9c_n0dwnr2799IeMzVHzt5kD4KbsZdF1fDStS-S-h5m61oH6kO1DPZrZTULL4UFk6DSGH5StMCSDqKbkxp2S6kKeIsS9ffGae-15v7kv4yl6Zgshzb321DzgwD7R_g6gev3fC66_kEQ5zM_XF-Qt1mMzwvhxUMQrOFA_GhuffvrMsDqmMlug42LKhg49a0Zk7yvfaCcwaB"),
    (20260901, 1788100000, 1788100000000, 1788100000891, 42,
     "0aqWtxUkM_Ve2qaynbKGpFKccXEXqNojqofYsO1Ywu5oWdNET8n9lxv9CdnK1YFSTqpUl_5CeklWvqkgVJNsYVN1fJlgnYldsJlXuyld0qlUnjjguycX2alw00Vb_BS_Qdg88upNYXY515HG9tiNLOquJfpivJjg4wyaK673tuEG95BG4VDL4-eGa2BYsqOBpHndgwzP2OGu-Xgv3QNnyoydeJlieYlBgpNTvtNCEwvuUGYvxEuv3QYNYvzSgQGwfbYlXPwna44ZWgscnp5dG574K8fV-qoPfTy92Vgpq0QInat5EWIuFrqADyaNPfHgTXydUufUqNtiQbV7hvsGAa4cztH6RQ0ef6Ag4ue24PKmTwU4Rjg9"),
]

API_URL = "https://apiv2.pinduoduo.com/api/gindex/tf/query_tf_goods_info"
TF_ID = "TFRQ0v00000Y_13396"


# ---------- 6. 备份路线：Node 补环境（generator/） ----------

def generate_node() -> str:
    """node generator/generate.js --json -> anti_content（s6vS HTTP 已 mock）。"""
    out = subprocess.run(
        ["node", os.path.join(GEN, "generate.js"), "--json"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=90, check=True)
    line = next(l for l in out.stdout.splitlines() if l.strip().startswith('{"success"'))
    return json.loads(line)["anti_content"]


def live_request(ac: str) -> tuple:
    """真实 API 请求: 返回 (status, success, goods_count, 首个商品名)。"""
    params = {"tf_id": TF_ID, "page": "1", "size": "3", "anti_content": ac}
    url = API_URL + "?" + urllib.parse.urlencode(params)
    headers = {
        "Accept": "application/json, text/javascript",
        "Origin": "https://www.pinduoduo.com",
        "Referer": "https://www.pinduoduo.com/",
        "User-Agent": UA,
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        status = resp.status
        data = json.loads(resp.read().decode("utf-8"))
    goods = data.get("result") or []
    name = goods[0].get("goods_name", "") if goods else ""
    return status, data.get("success") is True, len(goods), name


# ---------- 主流程 ----------

def main() -> None:
    passed, total = 0, 0

    def check(ok: bool, label: str, detail: str = "") -> None:
        nonlocal passed, total
        total += 1
        passed += ok
        print("[%s] %s %s" % ("PASS" if ok else "FAIL", label, detail))

    # 1. 序列化原语
    check(va(0) == b"\x00" and va(127) == b"\x7f" and va(128) == b"\x80\x01"
          and va(160000) == b"\x80\xe2\x09", "va() LEB128",
          "(0/127/128/160000)")
    check(nc(0) == b"\x00" and nc(255) == b"\xff" and nc(256) == b"\x01\x00",
          "nc() big-endian minimal", "(0/255/256)")
    check(ek(9, "ab") == b"\x4aab" and ek(14, 113) == b"\x71\x71"
          and ek(15, "x" * 111) == b"\x78\x6f" + b"x" * 111,
          "ek() tag/len encoding", "(short/int/long)")

    # 2. budget 编码器：全 64 索引双射 + 解码 roundtrip
    sample = build_payload(1788020797, 1788020797000, 1788020797113, 1,
                           random.Random(1))
    for v in (0, 1, 31, 63):
        enc = encode(sample + ET, v)
        check(enc[-1] == ALPHABET[v] and decode_anti_content("0aq" + enc) == sample + ET,
              "budget codec v=%d" % v, "(marker %s)" % enc[-1])

    # 3. 确定性向量：逐字节比对 + 解码结构 + zlib roundtrip
    for i, (seed, st, init_ms, now_ms, counter, expected) in enumerate(SAMPLE_CASES, 1):
        got = generate_anti_content(server_time=st, rng=random.Random(seed),
                                    init_ms=init_ms, now_ms=now_ms, counter=counter)
        ok, detail = check_anti_structure(got)
        check(got == expected, "vector #%d exact match" % i,
              "(%d chars)" % len(got))
        check(ok, "vector #%d structure" % i, detail)
        raw = decode_anti_content(got)
        payload = zlib.decompress(raw[:-4])
        check(zlib.compress(payload, 6) + ET == raw,
              "vector #%d zlib level 6 roundtrip" % i,
              "(head %s)" % raw[:2].hex())
        dev = parse_device_id(payload)
        check(len(dev.split("-")[0]) in (15, 16) and dev.endswith("-%d" % st),
              "vector #%d device_id format" % i, "(numeric + '-' + serverTime)")

    # 4. 同 seed 稳定 / 不同 seed 变化
    a1 = generate_anti_content(1788100000, random.Random(777), 1788100000000,
                               1788100000050, 2)
    a2 = generate_anti_content(1788100000, random.Random(777), 1788100000000,
                               1788100000050, 2)
    a3 = generate_anti_content(1788100000, random.Random(778), 1788100000000,
                               1788100000050, 2)
    check(a1 == a2 and a1 != a3, "determinism / seed sensitivity",
          "(same seed stable, different seed changes)")

    # 5. 备份路线：Node 原版引擎（--node）
    if "--node" in sys.argv:
        for i in (1, 2):
            ac = generate_node()
            ok, detail = check_anti_structure(ac)
            check(ok, "node generator #%d structure" % i, detail)
        check(True, "node route kept as backup", "(generator/ original bundle)")
    else:
        print("[SKIP] --node backup route (add --node, needs node)")

    # 6. 真实请求（--live，纯算法生成，不需要 node）
    if "--live" in sys.argv:
        status, success, count, name = live_request(generate_anti_content())
        check(status == 200 and success and count > 0, "live API request",
              "(HTTP %d, success=%s, %d goods: %s...)"
              % (status, success, count, name[:20]))
    else:
        print("[SKIP] --live real request (add --live, needs network)")

    print("\n%d/%d passed" % (passed, total))
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
