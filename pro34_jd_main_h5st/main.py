# -*- coding: utf-8 -*-
"""
京东主站 h5st v5.3 — 段结构 / seg7 编解码复现（部分复现）

结论（2026-08-30 逆向）:
    h5st = 10 段，以 ';' 分隔，总长 1103
      seg1 日期(17) seg2 fp(16) seg3 appId(5) seg4 token(92)
      seg5 hash(64) seg6 '5.3' seg7 环境JSON(788) seg8 hash块(64)
      seg9 hash(64) seg10 常量(32)

    seg7 = rev4( customBase64( rev3( PKCS7(JSON, 2空格缩进) ) ) )
    seg10 = 同一编码链("appid,body,functionId" + b'\\x03\\x03\\x03') = of7rHGH...

本文件验证: 10 段结构 + seg7 解码/重编码 + seg10 常量。
未包含: seg4/5/8/9 的哈希链 —— 主站 SDK 的 signer._algos.SHA256 是变体
(标准 hashlib 无法复现)，见 README「备注」。

运行: py main.py            # 3/3 通过（离线，仅标准库）
"""
import hashlib
import json
import sys

MAP1 = "rqponmlkjihgfedcbaZYXWVUTSRQPONMLKJIHGFEDCBA-_9876543210zyxwvuts"
MAP1_REV = {c: i for i, c in enumerate(MAP1)}

SEG10_PLAIN = b"appid,body,functionId\x03\x03\x03"
SEG10_CONST = "of7rHGHQ8GlOIyVOF6ZNHuFT-bVR7qUT"


def rev3(data):
    """每 3 字节块反转块序（尾部不足 3 字节的块保持原样）。"""
    blocks = [data[i:i + 3] for i in range(0, len(data), 3)]
    return b"".join(reversed(blocks))


def rev4(s):
    """每 4 字符组内逆序。"""
    return "".join(s[i:i + 4][::-1] for i in range(0, len(s), 4))


def custom_b64_encode(data):
    """SDK 的 _map1 自定义 base64（无 '=' 填充，尾部补零）。"""
    out = []
    for i in range(0, len(data), 3):
        b0 = data[i]
        b1 = data[i + 1] if i + 1 < len(data) else 0
        b2 = data[i + 2] if i + 2 < len(data) else 0
        n = (b0 << 16) | (b1 << 8) | b2
        out += [MAP1[(n >> 18) & 63], MAP1[(n >> 12) & 63],
                MAP1[(n >> 6) & 63], MAP1[n & 63]]
    return "".join(out)


def custom_b64_decode(s):
    bits = "".join(format(MAP1_REV[c], "06b") for c in s if c in MAP1_REV)
    return bytes(int(bits[i:i + 8], 2) for i in range(0, (len(bits) // 8) * 8, 8))


def pad_to_3(data):
    pad = (3 - len(data) % 3) % 3
    return data + bytes([pad]) * pad


def encode_seg7(env):
    """env dict → seg7（与浏览器 JSON.stringify(env, null, 2) 对齐）。"""
    raw = json.dumps(env, ensure_ascii=False, indent=2).encode("utf-8")
    return rev4(custom_b64_encode(rev3(pad_to_3(raw))))


def decode_seg7(seg):
    raw = rev3(custom_b64_decode(rev4(seg)))
    pad = raw[-1]
    if 1 <= pad <= 3 and raw.endswith(bytes([pad]) * pad):
        raw = raw[:-pad]
    return json.loads(raw.decode("utf-8"))


def encode_blob(data):
    """seg10 一类无 JSON 的短块：同样 rev3 → 自定义 base64 → rev4。"""
    return rev4(custom_b64_encode(rev3(data)))


def decode_blob(seg):
    return rev3(custom_b64_decode(rev4(seg)))


def split_h5st(h5st):
    parts = h5st.split(";")
    assert len(parts) == 10, "h5st 应为 10 段，实际 %d" % len(parts)
    return parts


# ---- 脱敏样例（真实捕获 2026-08-30；fp/canvas/webglFp 已替换为占位值） ----
ENV_SAMPLE = {
    "sua": "Windows NT 10.0; Win64; x64",
    "pp": {},
    "extend": {
        "wd": 0, "l": 0, "ls": 5, "wk": 0, "bu1": "0.1.4", "bu3": 41,
        "bu4": 0, "bu5": 0, "bu6": 28, "bu7": 0, "bu8": 0,
        "random": "NSTwQ341YB1", "bu12": -8, "bu10": 14, "bu11": 4, "bu13": "Fc",
    },
    "pf": "Win32",
    "random": "xOn9033SoS",
    "v": "h5_file_v5.3.4",
    "bu4": "0",
    "canvas": "0" * 32,
    "webglFp": "0" * 32,
    "ccn": 16,
    "bu14": "jmqmEtVELq",
    "t": 1788024996279,
    "fp": "sanitizedfp00001",
}

SEG7_SAMPLE = (
    "pjbMhjZf7rof7rESHWFNCaUR9m1PJrJdJrESJrpjh7Zd0jIeyHoe5rodzPYfLDIj3ipjLDrgJnkYmSmOm2VP_CFj"
    "LDIj3nYOJipjLDrg1nojxjJQIeFjLrJp-jpf7rof7rof7rof7rof7rof7rof7rof7rof7rof7rof7jpjxjpPl61S"
    "JW1OJrpjh7Jj7rof7rof7rof7rof7rof7rof7rof7rof7rof7rof7rIjLDIj4mFO9m1TJrpjh7Jj7jpjxjpe2iFjL"
    "rJp-jpe9fIg2T0UG6VRFuWeDipjxjJOJrpjh7JjYu1X4fofyz1YzipjxjZQ8aFQKiEjLrJp-jJf4zVRUipjxjJS7ip"
    "jLDrguqpjhj5Tlipjxj5f6XETJrpjLrJp-bojxjZf6XETJrpjLrJp-bYfLDIj7nYOJipjLrpjh7pd_rJdJjYf2iFjL"
    "rpjLDrgJnIbSmoe4n2OXeGYJrJdJ31QHyVT5ipjLrpjh7pfLDIjzXETJrpjLrJp-rojxj5e2iFjLrpjLDrgzjojxjJ"
    "e2iFjLrpjLDrg7rJdJXYOJipjLrpjh7pfLDIj3XETJrpjLrJp-noeLDIj4XETJrpjLrJp-jpe9nIg7jpjxjZf2iFjL"
    "rpjLDrg7rJdJ-1OJrpjLrJp-Xojxj5P-ipjLrpjh7pfLDIj-ipjLrpjh7pfLDIjHOEjLrpjLD7NLDIjHyVS3KUSJrpj"
    "h7ZMwqJdJrkPJrpjh7Jj3ToNL-oe1zVRUq5d7zpf6rpWdq5P0ulS9G1WJrJdJnVO4ipjLD7N"
)

H5ST_SAMPLE = (
    "20260830013641282;sanitizedfp00001;b5216;tk00" + "S" * 88 +
    ";a1bac14329dcafe6228fd9cc84719f3f64bc11ecbd43a78e43fd4339a6edb17c;"
    "5.3;1788024996282;" + SEG7_SAMPLE +
    ";32b3371be75abc8e0068a09007bf39f187484dcfc6031245367bd7944daf476d;" + SEG10_CONST
)

SEG10_SAMPLE = SEG10_CONST
H5ST_LENS = [17, 16, 5, 92, 64, 3, 13, 788, 64, 32]

SAMPLE_CASES = [
    {"kind": "seg10", "input": SEG10_SAMPLE, "plain": SEG10_PLAIN},
    {"kind": "seg7", "input": SEG7_SAMPLE, "env": ENV_SAMPLE},
    {"kind": "h5st", "input": H5ST_SAMPLE, "lens": H5ST_LENS},
]


def check(case):
    if case["kind"] == "seg10":
        got = decode_blob(case["input"])
        return got == case["plain"] and encode_blob(got) == case["input"], \
            "decode=%r reencode=ok" % got
    if case["kind"] == "seg7":
        env = decode_seg7(case["input"])
        re = encode_seg7(env)
        return env == case["env"] and re == case["input"], \
            "env_keys=%d reencode=%s" % (len(env), "ok" if re == case["input"] else "FAIL")
    parts = split_h5st(case["input"])
    lens = [len(x) for x in parts]
    env = decode_seg7(parts[7])
    ok = (lens == case["lens"] and parts[5] == "5.3" and parts[9] == SEG10_CONST
          and parts[0].isdigit() and parts[6].isdigit()
          and len(parts[0]) == 17 and len(parts[6]) == 13
          and env["fp"] == "sanitizedfp00001" and env["t"] == 1788024996279)
    return ok, "segments=%d lens=%s total=%d" % (len(parts), lens, len(case["input"]))


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--decode":
        env = decode_seg7(sys.argv[2].split(";")[7])
        print(json.dumps(env, ensure_ascii=False, indent=1))
        return

    passed = 0
    for case in SAMPLE_CASES:
        ok, info = check(case)
        passed += ok
        print("[%s] %-6s %s" % ("PASS" if ok else "FAIL", case["kind"], info))
    print("\n%d/%d 通过" % (passed, len(SAMPLE_CASES)))
    if passed != len(SAMPLE_CASES):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
