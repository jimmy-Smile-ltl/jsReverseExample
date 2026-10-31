# -*- coding: utf-8 -*-
"""
小红书 mns x3 签名纯算法复现（标准库，离线自验证）

链路（2026-08-31 与 VM 捕获逐字节一致，线上 200）:

    明文 89B → LE uint32 词 + 原始长度词 → XTEA(8 轮, delta=1013904243)
    → 96B 密文 → 标准 base64 6bit 分组 → F6 置换 → ALPHA64 查表
    → "mns0201_" + 128 字符

    c = uri + body；u = md5(c)；p = md5(uri)
    明文含版本头、rnd、毫秒时间戳、counter、c 长度、u/p 反码 XOR g、常量块

运行: py main.py     # 3 组真实 VM 样本 + 1 组字段构造向量
"""
import base64
import hashlib
import random
import struct

MASK = 0xFFFFFFFF
DELTA = 1013904243
ALPHA64 = "MfgqrsbcyzPQRStuvC7mn501HIJBo2DEYZajkl63Gp89+/A4UVFTKdeNOwxWXLhi"
KEY = [942945893, 845243187, 1701130593, 862270820]  # 'e6483ca2a1eed5e3' LE

_F6 = list(range(32))
_F6 += [v + 18 for v in range(32, 43)]
_F6 += [v - 11 for v in range(43, 46)]
_F6 += [v - 5 for v in range(46, 55)]
_F6 += [v + 6 for v in range(55, 58)]
_F6 += [v - 23 for v in range(58, 64)]
REV6 = {ALPHA64[_F6[i]]: i for i in range(64)}

CONST16 = bytes([1, 140, 248, 172, 103, 103, 201, 181, 129, 98, 93, 7, 68, 250, 132, 21])
W4 = 807840488          # 环境 DS 哈希（服务端不校验）
COUNTER = 521           # VM 全局调用计数（521 实测通过）


def i32(v):
    v &= MASK
    return v - 0x100000000 if v >= 0x80000000 else v


def R(e, x, a, j, n, key):
    """XTEA 轮函数（JS 位运算全 ToInt32 语义）。"""
    t1 = i32((a >> 5) ^ i32(x << 2)) + i32((x >> 3) ^ i32(a << 4))
    t2 = i32(e ^ x) + i32(key[(j & 3) ^ n] ^ a)
    return i32(i32(t1) ^ t2)


def xtea(words, key=KEY):
    l = len(words) - 1
    e = 0
    for _ in range(6 + 52 // len(words)):
        e = (e + DELTA) & MASK
        n = (e >> 2) & 3
        a = words[l]
        for j in range(l):
            words[j] = (words[j] + R(e, words[j + 1], a, j, n, key)) & MASK
            a = words[j]
        words[l] = (words[l] + R(e, words[0], a, l, n, key)) & MASK
    return words


def xtea_decrypt(words, key=KEY):
    l = len(words) - 1
    es = []
    e = 0
    for _ in range(6 + 52 // len(words)):
        e = (e + DELTA) & MASK
        es.append(e)
    for e in reversed(es):
        n = (e >> 2) & 3
        words[l] = (words[l] - R(e, words[0], words[l - 1], l, n, key)) & MASK
        for j in range(l - 1, 0, -1):
            words[j] = (words[j] - R(e, words[j + 1], words[j - 1], j, n, key)) & MASK
        words[0] = (words[0] - R(e, words[1], words[l], 0, n, key)) & MASK
    return words


def pack_bytes(b):
    """VM 的 _1c9208bc：LE uint32 词 + 末尾原始长度词。"""
    words = list(struct.unpack("<%dI" % (len(b) // 4), b[:len(b) // 4 * 4]))
    rem = b[len(b) // 4 * 4:]
    if rem:
        words.append(int.from_bytes(rem.ljust(4, b"\x00"), "little"))
    words.append(len(b))
    return words


def b64_encode(data):
    """标准 6bit 分组 → F6 置换 → ALPHA64 查表。"""
    bits = "".join(f"{b:08b}" for b in data)
    return "".join(ALPHA64[_F6[int(bits[i:i + 6].ljust(6, "0"), 2)]]
                   for i in range(0, len(bits), 6))


def b64_decode(s):
    bits = "".join(f"{REV6[ch]:06b}" for ch in s)
    return bytes(int(bits[i:i + 8], 2) for i in range(0, (len(bits) // 8) * 8, 8))


def gen_x3_from_plain(plaintext, key=KEY):
    words = xtea(pack_bytes(plaintext), key)
    return "mns0201_" + b64_encode(b"".join(struct.pack("<I", w) for w in words))


def decrypt_x3(x3, key=KEY):
    """x3 → 89 字节明文（逆 F6 + 逆 XTEA），用于结构验证。"""
    data = b64_decode(x3[8:])
    words = list(struct.unpack("<%dI" % (len(data) // 4), data))
    words = xtea_decrypt(words, key)
    return b"".join(struct.pack("<I", w) for w in words[:-1])[:words[-1]]


def build_plain(c, u, p, now, counter=COUNTER, rnd=None):
    """89 字节明文构造（c=uri+body, u=md5(c), p=md5(uri)）。"""
    if rnd is None:
        rnd = random.getrandbits(32)
    g = ((~rnd) & 0xFF) * 0x01010101
    out = bytearray([121, 104, 96, 41])
    out += struct.pack("<I", rnd)
    out += struct.pack("<I", now & 0xFFFFFFFF)
    out += struct.pack("<I", (now >> 32) & 0xFFFFFFFF)
    out += struct.pack("<I", W4)
    out += struct.pack("<I", 0)
    out += struct.pack("<I", 1)
    out += struct.pack("<I", counter)
    out += struct.pack("<I", len(c.encode()))
    out += struct.pack(">I", (~int(u[0:8], 16) & 0xFFFFFFFF) ^ g)
    out += struct.pack(">I", (~int(u[8:16], 16) & 0xFFFFFFFF) ^ g)
    out += bytes([3]) + b"unk"
    out += bytes([3]) + b"unk"
    c16 = bytearray(CONST16)
    c16[1] = 0x8C ^ ((~rnd) & 0xFF)
    out += bytes(c16) + bytes([3]) + b"nop" + bytes([16])
    for i in range(0, 32, 8):
        out += struct.pack(">I", (~int(p[i:i + 8], 16) & 0xFFFFFFFF) ^ g)
    assert len(out) == 89, len(out)
    return bytes(out)


def gen_x3(c, u, p, now_ms=None):
    if now_ms is None:
        import time
        now_ms = int(time.time() * 1000)
    return gen_x3_from_plain(build_plain(c, u, p, now_ms))


def _md5(s):
    return hashlib.md5(s.encode()).hexdigest()


# 真实 VM 样本（2026-08-31 pchook 捕获：89B 明文 → x3 逐字节一致）
SAMPLE_CASES = [
    {"kind": "plain", "plain": [121, 104, 96, 41, 18, 212, 236, 241, 118, 119, 202, 81, 160, 1, 0, 0, 232, 170, 38, 48, 0, 0, 0, 0, 1, 0, 0, 0, 10, 2, 0, 0, 33, 0, 0, 0, 107, 249, 40, 167, 152, 35, 187, 188, 3, 117, 110, 107, 3, 117, 110, 107, 1, 97, 248, 172, 103, 103, 201, 181, 129, 98, 93, 7, 68, 250, 132, 21, 3, 110, 111, 112, 16, 126, 163, 117, 168, 149, 243, 181, 68, 80, 31, 131, 125, 208, 38, 146, 46],
     "x3": "mns0201_elePYk5L7Z3YWhvfEzBWya4wMRM23o02888Bmw2QicqjEV0Dlcu/pGL+AjABv1PDbOMxG6Of+DzDZddPS1wNRTV3T40rozplasuUFp0QkM+g0Ihs5lVJnKaAG37xQbjo"},
    {"kind": "plain", "plain": [121, 104, 96, 41, 74, 211, 161, 65, 252, 166, 202, 81, 160, 1, 0, 0, 232, 170, 38, 48, 0, 0, 0, 0, 1, 0, 0, 0, 10, 2, 0, 0, 33, 0, 0, 0, 51, 161, 112, 255, 192, 123, 227, 228, 3, 117, 110, 107, 3, 117, 110, 107, 1, 57, 248, 172, 103, 103, 201, 181, 129, 98, 93, 7, 68, 250, 132, 21, 3, 110, 111, 112, 16, 38, 251, 45, 240, 205, 171, 237, 28, 8, 71, 219, 37, 136, 126, 202, 118],
     "x3": "mns0201_Fyw8UVv0VO/oHSU0KJQrCeid0b88wfdVAA7UaROditJIqP2P1XP5sSTQaOqEDvTlly5FU52ZBPhJ46X9mFBuTPzHC/0RttP4tpI0ePioSRDkNUOeC1hosX7q4YdkLpRm"},
    {"kind": "plain", "plain": [121, 104, 96, 41, 199, 141, 90, 8, 196, 214, 202, 81, 160, 1, 0, 0, 232, 170, 38, 48, 0, 0, 0, 0, 1, 0, 0, 0, 10, 2, 0, 0, 33, 0, 0, 0, 190, 44, 253, 114, 77, 246, 110, 105, 3, 117, 110, 107, 3, 117, 110, 107, 1, 180, 248, 172, 103, 103, 201, 181, 129, 98, 93, 7, 68, 250, 132, 21, 3, 110, 111, 112, 16, 171, 118, 160, 125, 64, 38, 96, 145, 133, 202, 86, 168, 5, 243, 71, 251],
     "x3": "mns0201_BzbJNUa+apsoUXlPWAZKoVDr32LSm0Hls6p6WLyBkcN/62o7t/9lCfWdUZV0X/Q754UPqBQsFvz5NPXKL7B/Zj+trHa2McwYb/ug9FyfwcbOCXB8rbEVAsOJwABQt2Vq"},
    # 字段构造向量：c/u/p + 固定时间/计数/随机 → 已知明文与 x3
    {"kind": "build", "c": '/api/sns/web/v1/homefeed{"num":1}',
     "u": "79eb3ab58a31a9ae9df79006df75f8a4",
     "p": "6cb167ba87e1a756420d916fc234803c",
     "now": 1322604864 | (416 << 32), "counter": 529, "rnd": 0x7FFFFFFF,
     "plain": [121, 104, 96, 41, 255, 255, 255, 127, 64, 89, 213, 78, 160, 1, 0, 0, 232, 170, 38, 48, 0, 0, 0, 0, 1, 0, 0, 0, 17, 2, 0, 0, 33, 0, 0, 0, 134, 20, 197, 74, 117, 206, 86, 81, 3, 117, 110, 107, 3, 117, 110, 107, 1, 140, 248, 172, 103, 103, 201, 181, 129, 98, 93, 7, 68, 250, 132, 21, 3, 110, 111, 112, 16, 147, 78, 152, 69, 120, 30, 88, 169, 189, 242, 110, 144, 61, 203, 127, 195],
     "x3": "mns0201_GnsxESOQmNSE87j4yi/83lgsOPAxT0QTagbr5FgfVynJPGvh6PHzYJ+RuWOxCDPunCvK1ERvxKu5Pbj4dOWhbLAwsmysCwfFjtvMAvYASmJTx71g3FOO+IJRr8QypnNF"},
]


def main():
    passed = 0
    for i, case in enumerate(SAMPLE_CASES, 1):
        if case["kind"] == "build":
            got_plain = build_plain(case["c"], case["u"], case["p"], case["now"],
                                    case["counter"], case["rnd"])
        else:
            got_plain = bytes(case["plain"])
        ok = got_plain == bytes(case["plain"])
        got_x3 = gen_x3_from_plain(got_plain)
        ok = ok and got_x3 == case["x3"] and decrypt_x3(case["x3"]) == got_plain
        counter = struct.unpack("<I", got_plain[28:32])[0]
        now = struct.unpack("<I", got_plain[8:12])[0] | (struct.unpack("<I", got_plain[12:16])[0] << 32)
        ok = ok and got_plain[:4] == bytes([121, 104, 96, 41]) and len(got_plain) == 89
        passed += ok
        print("[%s] case%d %-5s plain=%dB counter=%d time=%d"
              % ("PASS" if ok else "FAIL", i, case["kind"], len(got_plain), counter, now))
        print("       x3(%d)=%s..." % (len(got_x3), got_x3[:52]))
    print("\n%d/%d 通过" % (passed, len(SAMPLE_CASES)))
    if passed != len(SAMPLE_CASES):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
