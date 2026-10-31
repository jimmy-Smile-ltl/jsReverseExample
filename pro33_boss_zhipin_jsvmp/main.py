# -*- coding: utf-8 -*-
"""
BOSS直聘 __zp_stoken__ 纯算法复现（标准库，离线自验证）

链路:
    302 挑战 (seed/ts/name) -> JSVMP 生成 token -> 带上 Cookie 重放 200

    token = "523e" + "g" + base64(UTF8变体(变换链(head + X)))
    X[i] = (Y[i] + 3) ^ ord(str(key)[i % 5])
    Y    = [56] + t[k]+(k 或 2k) + ENV(186 项环境指纹)
    t    = [4] + ord("523e,") + ord(seed) + [240, ts_sec 4B, LCG()*100]

运行:
    py main.py              # 3 组固定向量 + 解码结构断言
    py main.py --gen SEED TS   # 生成一条当前时间的 token（需配合同轮 seed）

样例为 2026-08-29 线上版本 393d5208 的脱敏测试向量（seed 与时间均已过期）。
"""
import base64
import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))

_PREFIX_CHARS = [4, 53, 50, 51, 101, 44]   # [4] + ord("523e,")
_TOKEN_PREFIX = "523e" + "g"
_T_EXTRA_CONST = 240
_LCG_A, _LCG_C, _LCG_M, _LCG_DIV = 1664525, 1013904223, 2 ** 32, 2147483647

# 186 项生产环境指纹常量（沙箱固定值）
# env[113:117] 是生成时刻秒级时间戳（大端），env[151:154] 为其副本，运行时同步。
_ENV_CONST = json.load(open(os.path.join(HERE, "env_prod_const.json"), "r", encoding="utf-8"))


class LCG:
    """window.s 伪随机：s=(s*a+c)%2^32，输出 (s & 0x7FFFFFFF)/0x7FFFFFFF。"""

    def __init__(self, seed=None):
        self.s = seed if seed is not None else random.getrandbits(32)

    def next(self):
        self.s = (self.s * _LCG_A + _LCG_C) % _LCG_M
        return (self.s & _LCG_DIV) / _LCG_DIV


def utf8_2byte(chars):
    """VM 的 UTF-8 变体：<128 单字节，其余固定两字节（overlong 形式）。"""
    out = bytearray()
    for c in chars:
        if c < 128:
            out.append(c)
        else:
            out.append(0xC0 | (c >> 6))
            out.append(0x80 | (c & 63))
    return bytes(out)


def _decode_utf8_2byte(data):
    out, i = [], 0
    while i < len(data):
        b = data[i]
        if b < 0x80:
            out.append(b)
            i += 1
        else:
            out.append(((b & 0x1F) << 6) | (data[i + 1] & 0x3F))
            i += 2
    return out


def generate_token(seed, ts, lcg_seed=None, rand_fn=None, env_ts=None):
    """生成 __zp_stoken__。

    seed     : 302 挑战 URL 的 seed（44 字符 base64）
    ts       : 毫秒时间戳（东八区原始值）
    lcg_seed : 调试用固定 LCG 初始状态；None = 随机
    rand_fn  : 调试用替代 Math.random；None = 真随机
    env_ts   : 环境时间戳（秒）；None = 当前时间
    """
    rand = rand_fn or random.random
    lcg = LCG(lcg_seed)
    ts_sec = ts // 1000

    rand0_99 = int(lcg.next() * 100)

    t = list(_PREFIX_CHARS) + [ord(c) for c in seed]
    t += [_T_EXTRA_CONST,
          (ts_sec >> 24) & 0xFF, (ts_sec >> 16) & 0xFF,
          (ts_sec >> 8) & 0xFF, ts_sec & 0xFF, rand0_99]
    assert len(t) == 56, "t 长度 %d != 56（seed 应为 44 字符）" % len(t)

    y2 = [t[k] + (k if k % 2 == 0 else 2 * k) for k in range(56)]
    env = list(_ENV_CONST)
    now_sec = int(time.time()) if env_ts is None else int(env_ts)
    env[113:117] = [(now_sec >> 24) & 0xFF, (now_sec >> 16) & 0xFF,
                    (now_sec >> 8) & 0xFF, now_sec & 0xFF]
    env[151], env[152], env[153] = env[115], env[116], env[117]
    y2 += env
    assert len(y2) == 242, "Y2 长度 %d != 242（环境常量应为 186 项）" % len(y2)

    y = [56] + y2
    key = int(lcg.next() * 50000) + int(rand() * 50000)
    key_str = str(key)

    x = [(y[i] + 3) ^ ord(key_str[i % 5]) for i in range(243)]
    head = [192 + (key >> 16), (key >> 8) & 0xFF, key & 0xFF]
    payload_chars = [((((a + 12) ^ 3) + 5) ^ 1) for a in head + x]

    return _TOKEN_PREFIX + base64.b64encode(utf8_2byte(payload_chars)).decode()


def decode_token(token):
    """generate_token 的逆过程，用于结构验证（不依赖 seed/ts 原文）。"""
    assert token.startswith(_TOKEN_PREFIX), "前缀不是 523eg"
    chars = _decode_utf8_2byte(base64.b64decode(token[5:]))
    a0 = [((((p ^ 1) - 5) ^ 3) - 12) for p in chars]
    assert len(a0) == 246, "payload 长度 %d != 246" % len(a0)

    head, x = a0[:3], a0[3:]
    key = ((head[0] - 192) << 16) | (head[1] << 8) | head[2]
    key_str = str(key)
    y = [(x[i] ^ ord(key_str[i % 5])) - 3 for i in range(243)]
    assert y[0] == 56, "Y[0] 应为 56，实际 %d" % y[0]

    y2 = y[1:]
    t = [y2[k] - (k if k % 2 == 0 else 2 * k) for k in range(56)]
    assert t[:6] == _PREFIX_CHARS, "t 前缀不匹配"
    assert t[50] == _T_EXTRA_CONST, "t[50] 应为 240"
    ts_sec = (t[51] << 24) | (t[52] << 16) | (t[53] << 8) | t[54]

    env = y2[56:]
    assert len(env) == 186, "env 长度 %d != 186" % len(env)
    env_ts = (env[113] << 24) | (env[114] << 16) | (env[115] << 8) | env[116]
    assert (env[151], env[152], env[153]) == (env[115], env[116], env[117]), "时间副本未同步"

    return {
        "seed": "".join(chr(c) for c in t[6:50]),
        "ts_sec": ts_sec,
        "t55": t[55],
        "key": key,
        "env_ts": env_ts,
        "env": env,
    }


SEED = "bBgOxyc6pel8K+1v8TGkDvZBNLSCN4Ktt2kEJZ/GAJk="
ENV_TS = 1788022897

# (seed, ts_ms, lcg_seed, rand_seed, env_ts, 期望 token)
# 期望值由已线上验证的 JSVMP 生产链在固定随机源下生成（2026-08-29 版本）
SAMPLE_CASES = [
    (SEED, 1781494113632, 123456789, 42, ENV_TS,
     "523egw5Icw4IeTxwTHGsVb3dSY8ORwrRUdcOEw4xbfWBzwoLCp3nDh2nCqmnCq1taZ8ONUMOIVllUxInCv8OGwrzCvFPClX3CrlTCr8K+wqnEscO3YMO+w4HCs8OHwp9EOMOLxIfFhMWCxYnFisK4wqRaw4nDn8OEwpbFgsWJw6TCtMOhw4rFicWIxYnFhMWCxYnFiEBPREBRTkc1wrROQzVPSMOAccOAw4HDkcOLw4Mfw4Ymw5F/w4Alw4BzSCIlFW5uExYhHB8XZBVibnFnFRYeYh0WHG5uZm9lZXFrbHE3NMOEw7A4w4LEgzLDhsOrE8OCw5waw47DiDTDlWjCvDdSw4fCqiwyQkVAQ8OHxYRFQEtCR0VPTilRRENAQkJNQ045QjHDlmnCtTdUw4DEjilKTUZLR0c6Z0xCTUZDTkJLREY6Qko6OUXDgMOqw4XDqk5C"),
    (SEED, 1781494173632, 987654321, 7, ENV_TS,
     "523egw5XDpcO8H0kfHBhqG2x4VmLDh8K3W3nDicOGWHZkcsKIwqR6w4NkwqBmwqRfW3HDil/DjFdfV8SKwrvDh8K2wr9cwpl4wqRXwqDCusKkxKfDtG/DusOwXsOEwpBAPcOFxITFi8WGxYTFgMK7wqtew4TDmcOHwp3FhsWEw67Ct8OSw47FhMWCxYbFi8WGxYTFgkNAQEVHUUg5wrlEQD5LTcOKbsOPwr3DjMOFw4AQw4Inw4d8w48pw4V9SzEpEGRxHBIcFhwYYBBocWJjEBwhcSEXFnFlYm5rYmJvcWc0O8OAw7Uyw4XEjDbDh8OlEMORw5gbw4TDizvDmW3CtjRhw4PCqyY1UUlFTcOExYtJRUVFSElORCZCQEJKRVFRQkQ2US3Dl2/CsjhQw4XEhCZJUUdFREg+ZkZFRkJCREVEQEcwRUk+NEvDg8Opw4nDq0RF"),
    (SEED, 1781494233632, 555555555, 2026, ENV_TS,
     "523egw5XCusKTHEkaHx1tG217V2XDh8KyWHTDhsOGYXlpdcKIwqV9w4JnwqBjwqdeWHHDj1zDkVRfUsSNwrrDhMK2wrpfwpR7wqRSwqPCu8KnxKfDtWzDu8S3w4zDhcKTRTrDhcSFxYjFh8WHxYDCvsKoX8OHw5nDgsKaxYfFh8OuwrLDlcOPxYfFgsWDxYjFh8WHxYJGQ0VCR0hLNMK2RElBSkrDimvDjMK4w4/DhcOJE8ODJMOHfcOMJMOCfU4uJBNkaB8THxYdG2UTaGhlYhMcGG4cFBZoYmNxa2dlbm5nNTjDhcOyMsOExI83w4TDpRnDjsOdGMOEw444w5RqwrY1XsOCwqgmNE5EQk3DhcWIREJFREtEUUQjRUVFSkROTEVEM04ow5Rvwrc7VcOCxIQjRkxERUVLP2lGRElDRURER0VEMERGPzdLw4bDpsOEw6hERA=="),
]


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "--gen":
        print(generate_token(sys.argv[2], int(sys.argv[3])))
        return

    passed = 0
    for seed, ts, lcg_seed, rand_seed, env_ts, expected in SAMPLE_CASES:
        got = generate_token(seed, ts, lcg_seed, random.Random(rand_seed).random, env_ts)
        ok = got == expected
        info = decode_token(got)
        ok = ok and info["seed"] == seed and info["ts_sec"] == ts // 1000 \
            and info["env_ts"] == env_ts and 0 <= info["t55"] < 100
        passed += ok
        print("[%s] seed=%s... ts=%d lcg=%d rand=%d"
              % ("PASS" if ok else "FAIL", seed[:12], ts, lcg_seed, rand_seed))
        print("       token(%d)=%s..." % (len(got), got[:48]))
        print("       decode: key=%d env_ts=%d t55=%d" % (info["key"], info["env_ts"], info["t55"]))
        if not ok:
            print("       expected(%d)=%s..." % (len(expected), expected[:48]))
    print("\n%d/%d 通过" % (passed, len(SAMPLE_CASES)))
    if passed != len(SAMPLE_CASES):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
