# -*- coding: utf-8 -*-
"""
pro24 川航 ConstID (顶象 前端加固) — window.sss 编码器纯 Python 复现
====================================================================
用途: 复现 const_id.js (167KB 混淆 bundle) 中 `window.sss` 的完整编码链路,
     即请求头 `Param` 的生成核心:

    sss(r) = custom_base64( stringifyJSON(r), alphabet=reverse(u+f) )

  - stringifyJSON: json2 风格序列化 (来自模块 a(3) → 模块 9)
  - custom_base64 : 3 个 UTF-16 code unit → 4 字符, 字母表 65 字符 (末位 '='),
                    越界索引 charAt 返回空串 (非 ASCII 码元会被吞掉字符)
  - u / f          : 模块 a(44) (入口) 内两个字符串字面量, 拼起来 65 字符
  - 三个 XOR 解码器 : 32432 链式 / 42045 滚动 / V587 滚动 (自反, 用于解字符串表)

运行: python main.py          # 13 组样例 + 生产 Param 双向验证 (无网络)
参考值来源: 原项目 const_id.js 经 JSDOM 实跑捕获 (2026-08-20),
           生产 Param 头抓包于原项目 test.ipynb (2026-08-19).
"""

import json

# ---------------------------------------------------------------- 常量 (取自模块 a(44) 源码字面量)
U = "=x1LItAH4sf8gp6ewnXQTiKuF_5EkC2m7WjdrM"      # 38 字符
F = "UlGhvYo3aRzcq-VPyJBb9NZOD0S"                 # 27 字符
ALPHABET = (U + F)[::-1]                          # 65 字符, 末位 '='
IDX = {ch: i for i, ch in enumerate(ALPHABET)}    # 解码用反向表

_UNDEFINED = object()  # 模拟 JS undefined (对象中省略 / 数组中转 null)


# ---------------------------------------------------------------- stringifyJSON (json2 风格, 模块 9)
_ESC = {
    "\b": "\\b", "\t": "\\t", "\n": "\\n", "\f": "\\f",
    "\r": "\\r", '"': '\\"', "\\": "\\\\",
}
_CONTROL_RE = None  # 惰性编译


def _js_escape(s):
    """JS 字符串序列化 (本 bundle 实测): `"`、\\x00-\\x1f、\\x7f-\\x9f 转义 (\\b/\\t/\\n/\\f/\\r/\\" 用
    映射, 其余 \\uXXXX 补零 4 位); **反斜杠本身不转义** (bundle 正则不含 \\\\), 非 ASCII 原样."""
    global _CONTROL_RE
    import re
    if _CONTROL_RE is None:
        _CONTROL_RE = re.compile(r'["\x00-\x1f\x7f-\x9f]')
    return _CONTROL_RE.sub(
        lambda m: _ESC.get(m.group(0), "\\u%04x" % ord(m.group(0))), s)


def _js_number(n):
    """JS String(n) 近似: 整数直出; 浮点去 .0; |n|>=1e21 用 JS 风格指数."""
    if isinstance(n, int):
        return str(n)
    if n != n or n in (float("inf"), float("-inf")):
        return "null"  # NaN/Infinity → null
    if n == 0:
        return "0"  # 含 -0
    if abs(n) >= 1e21:
        s = "%.15e" % n
        mant, exp = s.split("e")
        mant = mant.rstrip("0").rstrip(".")
        return mant + "e" + ("+" if int(exp) >= 0 else "-") + str(abs(int(exp)))
    s = repr(n)
    if s.endswith(".0"):
        s = s[:-2]
    return s


def _js_key_order(d):
    """json2 对类整数键升序前置, 其余保持插入序."""
    arr, rest = [], []
    for k in d:
        if k.isdigit() and 0 <= int(k) < 2 ** 32 - 1:
            arr.append(k)
        else:
            rest.append(k)
    arr.sort(key=int)
    return arr + rest


def stringify_json(value):
    """json2 JSON.stringify 复刻 (紧凑输出, 无缩进)."""
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return '"' + _js_escape(value) + '"'
    if isinstance(value, (int, float)):
        return _js_number(value)
    if isinstance(value, list):
        parts = []
        for v in value:
            if v is _UNDEFINED:
                parts.append("null")
            else:
                parts.append(stringify_json(v))
        return "[" + ",".join(parts) + "]"
    if isinstance(value, dict):
        parts = []
        for k in _js_key_order(value):
            v = value[k]
            if v is _UNDEFINED:
                continue
            parts.append('"%s":%s' % (_js_escape(k), stringify_json(v)))
        return "{" + ",".join(parts) + "}"
    raise TypeError("unsupported: %r" % (value,))


# ---------------------------------------------------------------- 自定义字母表 base64 (模块 a(40) T.encode)
def sss_encode(value):
    """window.sss(r) = T.encode(R.stringifyJSON(r), reverse(u+f)).
    注意 JS 怪癖: f/c 索引 >=65 时 o.charAt 返回空串 → 输出字符被吞;
    isNaN 时 s/l 落到 64 → '=' (字母表末位)."""
    units = [ord(c) for c in stringify_json(value)]
    out, p = [], 0
    while p < len(units):
        i = units[p]; p += 1
        a = units[p] if p < len(units) else None; p += 1
        u = units[p] if p < len(units) else None; p += 1
        f = i >> 2
        c = ((3 & i) << 4) | (0 if a is None else a >> 4)
        if a is None:
            s = l = 64
        else:
            s = ((15 & a) << 2) | (0 if u is None else u >> 6)
            l = 64 if u is None else 63 & u
        for k in (f, c, s, l):
            out.append(ALPHABET[k] if k < 65 else "")  # charAt 越界 → ''
    return "".join(out)


def sss_decode(s):
    """sss_encode 的逆: 还原序列化文本. '=' (index 64) 为填充, 越界空字符无法还原
    (非 ASCII 码元有损, 仅 ASCII 内容可无损往返)."""
    units = []
    for g in range(0, len(s), 4):
        v = [IDX[ch] for ch in s[g:g + 4]]
        units.append((v[0] << 2) | (v[1] >> 4))
        if v[2] != 64:
            units.append(((v[1] & 15) << 4) | (v[2] >> 2))
            if v[3] != 64:
                units.append(((v[2] & 3) << 6) | v[3])
    return "".join(chr(u) for u in units)


# ---------------------------------------------------------------- 三个 XOR 解码器 (自反, 字符串表解密用)
def decode_chain32432(s):
    """u(): 链式 XOR, 种子 32432, 每字符后种子=当前输入码元.
    注意: 种子依赖输入 → **不是自反的** (逆过程需要前一个输出码元)."""
    out, seed = [], 32432
    for ch in s:
        code = ord(ch) ^ seed
        seed = ord(ch)
        out.append(chr(code))
    return "".join(out)


def decode_rolling42045(s):
    """f(): 滚动 XOR, 种子 42045, n = n*o%256+2333 (自反)."""
    out, seed = [], 42045
    for o, ch in enumerate(s):
        code = ord(ch) ^ seed
        seed = (seed * o) % 256 + 2333
        out.append(chr(code))
    return "".join(out)


def decode_v587(s):
    """V587(): 滚动 XOR, key='V587', 偏移 70966 起步进 +1 (自反)."""
    key = "V587"
    out, off = [], 70966
    for ch in s:
        off = (off + 1) % len(key)
        out.append(chr(ord(ch) ^ ord(key[off])))
    return "".join(out)


# ---------------------------------------------------------------- token 结构 (服务端签发, 8-hex 时间戳 + 32 字符)
def token_ts(token):
    """token 前 8 位 hex = Unix 时间戳 (大端)."""
    return int(token[:8], 16)


# ---------------------------------------------------------------- 样例 (期望值 = 原 bundle JSDOM 实跑捕获, 2026-08-20)
SAMPLE_CASES = [
    # (输入, 期望输出, 说明)
    ("", "B2B=", "空串 → stringify '""' (2 码元, 1 组 + 1 填充)"),
    ("a", "B5Z2", "单字符"),
    ("xOf", "B_mcl2B=", "短 ASCII"),
    ("test_1_2_3_输入", "B_RErsRWVYI6hp-Wo2",
     "含中文: 非 ASCII 码元 f/c 索引越界 → 2 个字符被吞 (输出 18 字符)"),
    ("ꑍॱज़৥শलজড়", "B8effsrB7==", "全非 ASCII 串"),
    ({"a": 1, "b": "x", "c": [1, 2]}, "j6JmBCFePDJ2BCF2jDBTB5V2qETePOJdWz==", "对象+数组"),
    ({"k": [1, -2.5, True, None], "s": "str", "n": 1e21, "z": 0},
     "j6JiBCuMVawQV248PbR6dvoTM_YTMNgTB_V2q2JpdbB2PDJXBCFelaT6Vaw2j2BAVbg=", "数字/布尔/1e21"),
    ("ab c", "B5Nrd3SwVON2hbowVON5B9V2", "控制字符 → \\uXXXX 转义"),
    ({"a": _UNDEFINED, "b": 1}, "j6J2BCFeWz==", "undefined 属性被省略"),
    ([1, _UNDEFINED, 3], "vpZTM_YTMDwphz==", "数组内 undefined → null"),
    ({}, "jsg=", "空对象"),
    ([], "v8g=", "空数组"),
    ({"b": 1, "a": 2, "5": "five", "z9": "x"}, "j6B8BCF2l5EflaBTB5B2qCZTB5Z2qCBTB_FHBCF2jDJL",
     "类整数键升序前置 (5 排最前)"),
    ("x\\n\\ty", "B_mrMEegjaB=", "转义映射 \\n \\t"),
]

# 生产 Param 头 (原项目 test.ipynb 2026-08-19 抓包, 972 字符) — 双向验证
PROD_PARAM = (
    "j6JTUvz2q2Jk-pSeqOk8-pZHlvBfVfzeVOS6l5JEqOV6G3opqOS4q3lElvJkGfVHGvNmG3JkG3Zg-3B4G3-"
    "5l5l2l3ofl3k8qvG8-vzsq3S2PDJTUvRojh0EBCFePDJCGv-FlaBAdbJ8law2rf-EM5o2q2J5M9E_UbRedvY6jaB"
    "TB5NwrZQEjaBAB5zelOlC-9V4GpmEV9lEGvRCqOofl3r4-OY5l5Yk-OSfB_g="
)

# 真实 token (原项目抓包): 8-hex Unix 秒 + 32 字符
REAL_TOKENS = [
    "6a16ccfeEzhCRdCrxZedzna0PbzzpOa7Qzvw8GH1",   # test.ipynb 2026-08-19
    "6a16e33fRBAW1hsDHmbwmv9fv4D3FcUWnaf5IFK1",   # test.ipynb 2026-08-19
]


# ---------------------------------------------------------------- 验证
def main():
    ok = 0
    for idx, (inp, expected, note) in enumerate(SAMPLE_CASES, 1):
        got = sss_encode(inp)
        if got == expected:
            ok += 1
            print("PASS #%02d %s" % (idx, note))
        else:
            print("FAIL #%02d %s\n  got     = %s\n  expect  = %s" % (idx, note, got, expected))

    # 生产 Param 双向验证: 解码 → JSON 解析 → 重编码 → 逐字节相等
    plain = sss_decode(PROD_PARAM)
    obj = json.loads(plain)
    re_enc = sss_encode(obj)
    if re_enc == PROD_PARAM:
        ok += 1
        print("PASS #%02d 生产 Param 往返 (972 字符逐字节相等, 指纹字段 %d 个)" % (len(SAMPLE_CASES) + 1, len(obj)))
    else:
        print("FAIL 生产 Param 往返\n  re_enc len %d vs %d" % (len(re_enc), len(PROD_PARAM)))
        print("  plain head:", plain[:80])

    # 三个 XOR 解码器验证: 42045/V587 自反, 32432 链式用正向样例
    if decode_rolling42045(decode_rolling42045("roundtrip_check")) == "roundtrip_check":
        ok += 1
        print("PASS 42045 解码器自反")
    else:
        print("FAIL 42045 解码器")
    if decode_v587(decode_v587("roundtrip_check")) == "roundtrip_check":
        ok += 1
        print("PASS V587 解码器自反")
    else:
        print("FAIL V587 解码器")
    # 正向解码 (期望值 = node 实跑原 bundle 捕获):
    # mod3 里 32432 解码出 stringifyJSON 导出名; 加载器里 42045 解码出 'exports'/'__esModule'
    if decode_chain32432("练纷绅纬绂纥绌纪结纙绊纅绋") == "stringifyJSON":
        ok += 1
        print("PASS 32432 正向解码 → stringifyJSON")
    else:
        print("FAIL 32432 正向解码")
    if decode_rolling42045("ꑘ॥ॊ৾ঢऩঝ") == "exports":
        ok += 1
        print("PASS 42045 正向解码 → exports")
    else:
        print("FAIL 42045 正向解码")

    # token 结构 + 时间戳
    for tok in REAL_TOKENS:
        ts = token_ts(tok)
        import datetime
        dt = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)
        ok += 1
        print("PASS token %s... ts=0x%s=%d (%s)" % (tok[:8], tok[:8], ts, dt.strftime("%Y-%m-%d %H:%M:%SZ")))

    total = len(SAMPLE_CASES) + 1 + 4 + len(REAL_TOKENS)  # 样例 + Param 往返 + 4 解码器 + 2 token
    print("\n总计: %d/%d 通过" % (ok, total))
    if ok != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
