# -*- coding: utf-8 -*-
"""
抖音 a_bogus 纯 Python 实现（标准库，零 Node/浏览器依赖）

算法组成：SM3（国密）+ RC4 变体混淆 + 双字母表自定义 Base64 + 44 值流结构。

    inner = UA 经 RC4 变体混淆 → encryptionUa(base64)
    arr29 = 时间/参数/请求体/UA 的 SM3 摘要 + 随机填充位 → RC4 变体混淆
    sig   = customB64(topHeaderRandom + ABgarbled(arr29))   # 196 字符

运行：py main.py     # 3 组固定向量（mulberry32 seed + 固定时间戳）
说明：随机域/填充位是真随机，服务端不校验；固定随机源只为可复现。
"""
import random as _random
import time as _time

__all__ = ['get_abogus']

# 主签名 Base64 字母表 (getABogus)
B64_CHARS = "Dkdpgh2ZmsQB80/MfvV36XI1R45-WUAlEixNLwoqYTOPuzKFjJnry79HbGcaStCe"
# UA 加密 Base64 字母表 (encryptionUa)
UA_B64_CHARS = "ckdp1h4ZKsUB80/Mfvw36XIgR25+WQAlEi7NLboqYTOPuzmFjJnryx9HVGDaStCe"

DEFAULT_UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
              'AppleWebKit/537.36 (KHTML, like Gecko) '
              'Chrome/148.0.0.0 Safari/537.36')

# encodeURIComponent 不编码的字符集 (ECMA-262 规范)
_URI_SAFE = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.!~*'()")


def _js_bytes(s: str) -> bytes:
    """复刻 JS: encodeURIComponent(e) → %XX 还原为 char → charCodeAt
    即: 安全字符取 ASCII 码, 其余取 UTF-8 字节"""
    out = bytearray()
    for ch in s:
        if ch in _URI_SAFE:
            out.append(ord(ch))
        else:
            out += ch.encode('utf-8')
    return bytes(out)


# ==================== SM3 (国密哈希) ====================
_SM3_IV = (0x7380166F, 0x4914B2B9, 0x172442D7, 0xDA8A0600,
           0xA96F30BC, 0x163138AA, 0xE38DEE4D, 0xB0FB0E4E)


def _rotl(x, n):
    n %= 32
    if n == 0:
        return x & 0xFFFFFFFF
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF


def sm3(msg: bytes) -> bytes:
    bit_len = len(msg) * 8
    msg = msg + b'\x80'
    msg = msg + b'\x00' * ((56 - len(msg) % 64) % 64)
    msg = msg + bit_len.to_bytes(8, 'big')
    v = list(_SM3_IV)
    for off in range(0, len(msg), 64):
        block = msg[off:off + 64]
        w = [int.from_bytes(block[i * 4:i * 4 + 4], 'big') for i in range(16)]
        for j in range(16, 68):
            x = w[j - 16] ^ w[j - 9] ^ _rotl(w[j - 3], 15)
            x = x ^ _rotl(x, 15) ^ _rotl(x, 23)
            w.append((x ^ _rotl(w[j - 13], 7) ^ w[j - 6]) & 0xFFFFFFFF)
        w1 = [w[j] ^ w[j + 4] for j in range(64)]
        a, b, c, d, e, f, g, h = v
        for j in range(64):
            tj = 0x79CC4519 if j < 16 else 0x7A879D8A
            ss1 = _rotl((_rotl(a, 12) + e + _rotl(tj, j)) & 0xFFFFFFFF, 7)
            ss2 = ss1 ^ _rotl(a, 12)
            if j < 16:
                ff, gg = a ^ b ^ c, e ^ f ^ g
            else:
                ff, gg = (a & b) | (a & c) | (b & c), (e & f) | ((~e) & g)
            tt1 = (ff + d + ss2 + w1[j]) & 0xFFFFFFFF
            tt2 = (gg + h + ss1 + w[j]) & 0xFFFFFFFF
            d, c, b, a = c, _rotl(b, 9), a, tt1
            h, g, f, e = g, _rotl(f, 19), e, (tt2 ^ _rotl(tt2, 9) ^ _rotl(tt2, 17)) & 0xFFFFFFFF
        v = [(x ^ y) & 0xFFFFFFFF for x, y in zip(v, (a, b, c, d, e, f, g, h))]
    return b''.join(x.to_bytes(4, 'big') for x in v)


def get_arr(t):
    """对应 JS get_arr(t, a) 默认分支 (a 非 'hex'):
    字符串 → _js_bytes → SM3;  字节序列 → SM3"""
    if isinstance(t, str):
        return sm3(_js_bytes(t))
    return sm3(bytes(t))


# ==================== RC4 变体混淆 ====================
def ab_arr_256():
    nums = list(range(255, -1, -1))
    prev = 0
    lm = 211  # String.fromCharCode(211)
    for i in range(256):
        prev = (prev * nums[i] + prev + lm) % 256
        nums[i], nums[prev] = nums[prev], nums[i]
    return nums


def ab_garbled(s):
    arr = ab_arr_256()
    n4 = 0
    ans = []
    for i, ch in enumerate(s):
        n2 = (i + 1) % 256
        n4 = (n4 + arr[n2]) % 256
        old = arr[n2]
        arr[n2], arr[n4] = arr[n4], old
        n7 = (arr[n2] + old) % 256
        ans.append(chr(ord(ch) ^ arr[n7]))
    return ''.join(ans)


def ua_arr_256(ua_salt):
    nums = list(range(255, -1, -1))
    prev = 0
    lm = (0, 1, ua_salt)  # String.fromCharCode(0.00390625, 1, ua_salt)
    for i in range(256):
        prev = (prev * nums[i] + prev + lm[i % 3]) % 256
        nums[i], nums[prev] = nums[prev], nums[i]
    return nums


def ua_garbled(ua, ua_salt):
    arr = ua_arr_256(ua_salt)
    n4 = 0
    ans = []
    for i, ch in enumerate(ua):
        n2 = (i + 1) % 256
        n4 = (n4 + arr[n2]) % 256
        old = arr[n2]
        arr[n2], arr[n4] = arr[n4], old
        n7 = (arr[n2] + old) % 256
        ans.append(chr(ord(ch) ^ arr[n7]))
    return ''.join(ans)


# ==================== 自定义 Base64 ====================
def _custom_b64(s, chars):
    out = []
    j = 0
    n = len(s)
    i = 0
    while i <= n:
        if i + 3 <= n:
            c0, c1, c2 = ord(s[i]), ord(s[i + 1]), ord(s[i + 2])
            v = c2 | c1 << 8 | c0 << 16
            out.append(chars[(v & 16515072) >> 18])
            out.append(chars[(v & 258048) >> 12])
            out.append(chars[(v & 4032) >> 6])
            out.append(chars[v & 63])
        elif i + 3 > n:
            u = n - j
            if u == 2:
                c0, c1 = ord(s[j]), ord(s[j + 1])
                v = c1 << 8 | c0 << 16
                out.append(chars[(v & 16515072) >> 18])
                out.append(chars[(v & 258048) >> 12])
                out.append(chars[(v & 4032) >> 6])
                out.append('=')
            if u == 1:
                c0 = ord(s[j])
                v = c0 << 16
                out.append(chars[(v & 16515072) >> 18])
                out.append(chars[(v & 258048) >> 12])
                out.append('==')
        j += 3
        i += 3
    return ''.join(out)


def encryption_ua(ss):
    return _custom_b64(ss, UA_B64_CHARS)


# ==================== 结构组装 ====================
def get_arr2(ua):
    if 'Win' not in ua:  # JS: userAgent.indexOf('Win') === -1
        data = '2056|1080|2056|1201|2056|1201|2056|1329|MacIntel'
    else:
        data = '2056|1080|2056|1201|2056|1201|2056|1329|Win32'
    return [ord(c) for c in data]


def get_last_3num(d1):
    s = str((int(d1) + 3) & 0xFF) + ","
    return [ord(c) for c in s]


# getLastNum2 的 arr 索引 (跳过 24/28/32/49/52)
_XOR_ARR_IDX = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17,
                18, 19, 20, 21, 22, 23, 25, 26, 27, 29, 30, 31, 33, 34, 35, 36,
                37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 50, 51, 53, 54]


def get_last_num2(arr0, arr):
    x = 0
    for v in arr0[:8]:
        x ^= v
    for idx in _XOR_ARR_IDX:
        x ^= arr[idx]
    return x


def get_num_list(arr0, arr_ar, rand):
    num_list = []
    i, n = 0, len(arr_ar)
    while i < n:
        if i + 2 >= n:
            if i + 1 >= n:
                num_list.append(arr_ar[i])
            else:
                num_list.append(arr_ar[i])
                num_list.append(arr_ar[i + 1])
        else:
            r = int(rand() * 1000) & 255
            num_list.append((r & 145) | (arr_ar[i] & 110))
            num_list.append((r & 66) | (arr_ar[i + 1] & 189))
            num_list.append((r & 44) | (arr_ar[i + 2] & 211))
            num_list.append(
                ((arr_ar[i] & 145) | (arr_ar[i + 1] & 66)) | (arr_ar[i + 2] & 44))
        i += 3
    return list(arr0) + num_list


def top_header_random(rand):
    num1 = int(rand() * 65535) & 255
    num2 = int(rand() * 40)  # Math.random() * 40 >> 0
    return ''.join(chr(x) for x in [
        (num1 & 170) | (3 & 85),
        (num1 & 85) | (3 & 170),
        (num2 & 170) | (82 & 85),
        (num2 & 85) | (82 & 170),
    ])


def random_garbled_list(rand):
    # randomGarbledCharactersArray1
    r1 = int(rand() * 65535)
    n1, n2 = r1 & 255, (r1 >> 8) & 255
    arr = [(n1 & 170) | (1 & 85), (n1 & 85) | (1 & 170),
           (n2 & 170) | (0 & 85), (n2 & 85) | (0 & 170)]
    # randomGarbledCharactersArray2
    n1 = int(rand() * 240)
    n2 = (int(rand() * 255) & 77) | 2 | 16 | 32 | 128
    arr += [(n1 & 170) | (1 & 85), (n1 & 85) | (1 & 170),
            (n2 & 170) | (0 & 85), (n2 & 85) | (0 & 170)]
    return arr


# get_arr29 的 arr2 排列索引 (共 50 项)
_ARR2_PERM = [9, 18, 30, 35, 47, 4, 44, 19, 10, 23, 12, 40, 25, 42, 3, 22, 38,
              21, 5, 45, 1, 29, 6, 43, 33, 14, 36, 37, 2, 46, 15, 48, 31, 26,
              16, 13, 8, 41, 27, 17, 39, 20, 11, 0, 34, 7, 50, 51, 53, 54]


def get_arr29(d1, d2, params, data, ua, now, rand):
    par_arr = get_arr(get_arr(params))
    data_arr = get_arr(get_arr(data))
    ua_salt = 0  # JS switch 两分支均为 0
    browser_arr = get_arr(encryption_ua(ua_garbled(ua, ua_salt)))
    arr = [0] * 55
    num = get_arr2(ua)
    d3 = int((now() - 1721836800000) / 1000 / 60 / 60 / 24 / 14)  # JS >> 0
    arr0 = random_garbled_list(rand)

    d1i, d2i = int(d1), int(d2)
    arr[0] = 41
    arr[1] = d3
    arr[2] = 5
    arr[3] = (d1i - d2i + 3) & 255
    arr[4] = d1i & 255
    arr[5] = (d1i & 0xFFFFFFFF) >> 8 & 255
    arr[6] = (d1i & 0xFFFFFFFF) >> 16 & 255
    arr[7] = (d1i & 0xFFFFFFFF) >> 24 & 255
    arr[8] = int(d1 / (2 ** 32)) & 255
    arr[9] = int(d1 / (2 ** 40)) & 255
    arr[10] = 1 % 256 & 255
    arr[11] = 0  # 1 / 256 & 255
    arr[12] = 1 & 255
    arr[13] = 0  # 1 >> 8 & 255
    arr[14] = 1
    arr[15] = arr[16] = arr[17] = 0
    arr[18] = ua_salt & 255
    arr[19] = ua_salt >> 8 & 255
    arr[20] = ua_salt >> 16 & 255
    arr[21] = ua_salt >> 24 & 255
    arr[22] = par_arr[9]
    arr[23] = par_arr[18]
    arr[24] = 3
    arr[25] = par_arr[3]
    arr[26] = data_arr[10]
    arr[27] = data_arr[19]
    arr[28] = 4
    arr[29] = data_arr[4]
    arr[30] = browser_arr[11]
    arr[31] = browser_arr[21]
    arr[32] = 5
    arr[33] = browser_arr[5]
    arr[34] = d2i & 255
    arr[35] = (d2i & 0xFFFFFFFF) >> 8 & 255
    arr[36] = (d2i & 0xFFFFFFFF) >> 16 & 255
    arr[37] = (d2i & 0xFFFFFFFF) >> 24 & 255
    arr[38] = int(d2 / (2 ** 32)) & 255
    arr[39] = int(d2 / (2 ** 40)) & 255
    arr[40] = 3
    arr32 = 6241
    arr[41] = arr32 & 255
    arr[42] = arr32 >> 8 & 255
    arr[43] = arr32 >> 16 & 255
    arr[44] = arr32 >> 24 & 255
    arr36 = 6383
    arr[45] = arr36 & 255
    arr[46] = arr36 >> 8 & 255
    arr[47] = arr36 >> 16 & 255
    arr[48] = arr36 >> 24 & 255
    last_num_one = get_last_3num(d1)
    arr[49] = len(num)
    arr[50] = len(num) & 255
    arr[51] = len(num) >> 8 & 255
    arr[52] = len(last_num_one)
    arr[53] = len(last_num_one) & 255
    arr[54] = len(last_num_one) >> 8 & 255
    last_num = get_last_num2(arr0, arr)

    arr2 = [arr[i] for i in _ARR2_PERM]
    new_arr = arr2 + num
    new_arr2 = new_arr + last_num_one
    new_arr2.append(last_num)
    return get_num_list(arr0, new_arr2, rand)


def get_garbled_string(params, data, ua, now, rand):
    t1 = now()  # Date.now() #1
    t2 = t1 - int(rand() * 10)
    arr_29 = get_arr29(t1, t2, params, data, ua, now, rand)
    a = top_header_random(rand)
    b = ab_garbled(''.join(chr(v) for v in arr_29))
    return a + b


def get_abogus(params_str, data=None, user_agent=None, rand=None, now=None):
    """生成 a_bogus

    Args:
        params_str: urlencode 后的请求参数字符串
        data: POST body 字符串, GET 为 None
        user_agent: 与请求头一致的 UA
        rand: 可注入的随机源 callable → [0,1) float (测试用)
        now: 可注入的时间源 callable → 毫秒时间戳 (测试用)
    """
    rand = rand if rand is not None else _random.random
    now = now if now is not None else (lambda: int(_time.time() * 1000))
    user_agent = user_agent or DEFAULT_UA
    params = params_str + "dhzx"
    data = (data or "") + "dhzx"
    garbled = get_garbled_string(params, data, user_agent, now, rand)
    return _custom_b64(garbled, B64_CHARS)


# ==================== 确定性 PRNG (mulberry32, 与 parity_harness.js 一致) ====================
class Mulberry32:
    """复刻 parity_harness.js 注入的确定性随机源"""

    def __init__(self, seed):
        self.a = seed & 0xFFFFFFFF

    def __call__(self):
        a = self.a
        a = (a + 0x6D2B79F5) & 0xFFFFFFFF
        self.a = a
        t = ((a ^ (a >> 15)) * (1 | a)) & 0xFFFFFFFF  # Math.imul
        t = ((t + ((t ^ (t >> 7)) * (61 | t) & 0xFFFFFFFF)) ^ t) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296


SAMPLE_CASES = [
    # GET：作品列表基础参数（sec_user_id 已脱敏）
    ("device_platform=webapp&aid=6383&channel=channel_pc_web"
     "&sec_user_id=MS4wLjABAAAASANITIZEDUSERID000000000000000000000000000000000000000"
     "&max_cursor=0&count=18&version_code=290100&version_name=29.1.0",
     None,
     "my0jDFSwQx8ReVFtuCppelFlxyfArT8yrPiKRteTSV-IyZ0b3uPcOcS-jxw8sXIh0mMiw1178xtMbDxcq4Uzp9rpFmkfSEhSFsI9Ih8oh1qkbeT0grfhCLuNeJGT05tEzOKyJAWIA08aIxcULqNhUn5HH/ixsmkdFNH9pdWGO2F1ItT9PrqduxGdTXzOBOo5Bj=="),
    # GET：关键词搜索
    ("aid=6383&keyword=food+review&max_cursor=0&count=18", None,
     "my0jDFSwQx8ReVFtuCppelFlxyfArT8yjBiKSGMTS3lnyZMb3uPcOcS-jxw8sXIh0mMiw1178xtMbDxcq4Uzp9rpFmkfSEhSFsI9Ih8oh1qkbeT0grfhCLuNeJGT05tEzOKyJAWIA08aIxcULqNhUn5HH/ixsmkdFNH9pdWGO2F1ItT9PrqduxGdTXzOBOo5VD=="),
    # POST：body 参与签名
    ("aid=6383&count=18", '{"keyword":"food","page":1}',
     "my0jDFSwQx8ReVFtuCppelFlxyfArT8yjPiKWTqTSV5VyZMT3uPcOCW-jxw8sXIh0mMiw1178xSkbDxcq4UzQ9rpFmkfSEhSFsI9Ih8oh1qkbeT0grfhCLuNeJGT05tEzOKyJAWIA08aIxcULqNhUn5HH/ixsmkdFNH9pdWGO2F1ItT9PrqduxGdTXzOBOo5Ej=="),
]


def main():
    ok_sm3 = sm3(b'abc').hex() == \
        '66c7f0f462eeedd9d1f2d46bdc10e4e24167c4875cf2f7a2297da02b8f4ba8e0'
    ok_bytes = _js_bytes('测A!') == b'\xe6\xb5\x8bA!'
    print("[%s] SM3('abc') 国密标准向量" % ("PASS" if ok_sm3 else "FAIL"))
    print("[%s] encodeURIComponent 字节语义" % ("PASS" if ok_bytes else "FAIL"))
    if not (ok_sm3 and ok_bytes):
        raise SystemExit(1)

    passed = 0
    for params, data, expected in SAMPLE_CASES:
        got = get_abogus(params, data=data, user_agent=DEFAULT_UA,
                         rand=Mulberry32(12345), now=lambda: 1788022897000)
        ok = got == expected and len(got) == 196
        passed += ok
        print("[%s] %s data=%s" % ("PASS" if ok else "FAIL", params[:52],
                                   (data or "-")[:24]))
        print("       a_bogus(%d)=%s..." % (len(got), got[:56]))
    print("\n%d/%d 通过" % (passed, len(SAMPLE_CASES)))
    if passed != len(SAMPLE_CASES):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
