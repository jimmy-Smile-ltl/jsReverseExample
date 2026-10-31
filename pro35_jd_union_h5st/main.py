# -*- coding: utf-8 -*-
"""
京东联盟 h5st 纯算法复现（标准库，离线自验证）

2026-08-30 成果：与 Node 补环境 SDK 输出逐字节一致（10/10 段）。

    seg1  yyyyMMddHHmmssSSS (17)
    seg2  fp (16)
    seg3  appId (5)
    seg4  token (92)
    seg5  SHA256(X + stkStr + X + salt5)
          X = SHA256(token + fp + ts19 + appId + rd)
          stkStr = "appid:<appid>&body:<bodyJson>&functionId:<functionId>"
    seg6  "5.3"
    seg7  ts13 (13)
    seg8  rev4(customB64(rev3(JSON indent=2 + PKCS7)))
    seg9  SHA256(X + "appid:appid&functionid:functionId" + X + salt9)
    seg10 rev4(customB64(rev3("appid,body,functionId" + b"\\x03"*3))) = of7rHGH...

运行: py main.py     # 3 组确定性向量（固定盐/随机串/时间戳）
"""
import hashlib
import json
import random
import string
import time

MAP1 = "rqponmlkjihgfedcbaZYXWVUTSRQPONMLKJIHGFEDCBA-_9876543210zyxwvuts"
MAP1_REV = {c: i for i, c in enumerate(MAP1)}
SEG10_CONST = "of7rHGHQ8GlOIyVOF6ZNHuFT-bVR7qUT"


def custom_b64_encode(data):
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


def rev3(data):
    blocks = [data[i:i + 3] for i in range(0, len(data), 3)]
    return b"".join(reversed(blocks))


def rev4(s):
    return "".join(s[i:i + 4][::-1] for i in range(0, len(s), 4))


def pad_to_3(data):
    pad = (3 - len(data) % 3) % 3
    return data + bytes([pad]) * pad


def rand36(n):
    alphabet = string.ascii_letters + string.digits + "-"
    return "".join(random.choice(alphabet) for _ in range(n))


def encode_seg8(obj):
    raw = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
    return rev4(custom_b64_encode(rev3(pad_to_3(raw))))


def decode_seg8(seg):
    raw = rev3(custom_b64_decode(rev4(seg)))
    pad = raw[-1]
    if 1 <= pad <= 3 and raw.endswith(bytes([pad]) * pad):
        raw = raw[:-pad]
    return json.loads(raw.decode("utf-8"))


def gen_h5st(function_id, appid, body, fp, token, app_id="586ae",
             rd="zfUFWJ0sxS65", webgl_fp="0" * 32, canvas="0" * 32,
             bu14="EEmjRVVELq", ts19=None, ts13=None, salt5=None, salt9=None,
             random1=None, random2=None, t=None):
    """生成 1103 字符 h5st。传入 ts19/ts13/盐/随机串即为确定性模式。"""
    if ts19 is None:
        now = time.localtime()
        ts19 = time.strftime("%Y%m%d%H%M%S", now) + "%03d" % (int(time.time() * 1000) % 1000) + "54"
    d = ts19[:17]
    ts13 = ts13 or int(time.time() * 1000)

    body_json = json.dumps({**body, "clientPageId": "jingfen_pc"},
                           ensure_ascii=False, separators=(",", ":"))

    X = hashlib.sha256(("%s%s%s%s%s" % (token, fp, ts19, app_id, rd)).encode()).hexdigest()
    stk_str = "appid:%s&body:%s&functionId:%s" % (appid, body_json, function_id)
    salt5 = salt5 or (rand36(7) + "RvI<7|")
    salt9 = salt9 or (rand36(7) + "RvI<7|")
    seg5 = hashlib.sha256(("%s%s%s%s" % (X, stk_str, X, salt5)).encode()).hexdigest()
    seg9 = hashlib.sha256(("%sappid:appid&functionid:functionId%s%s"
                           % (X, X, salt9)).encode()).hexdigest()

    plain = {
        "sua": "Windows NT 10.0; Win64; x64",
        "pp": {},
        "extend": {
            "wd": 0, "l": 0, "ls": 5, "wk": 64, "bu1": "0.1.5", "bu3": -1,
            "bu4": 0, "bu5": 0, "bu6": -1, "bu7": 1, "bu8": 4,
            "random": random1 or rand36(11), "bu12": -8, "bu10": 14,
            "bu11": 3, "bu13": "Fy",
        },
        "pf": "Win32",
        "random": random2 or rand36(11),
        "v": "h5_file_v5.3.4",
        "bu4": "0",
        "canvas": canvas,
        "webglFp": webgl_fp,
        "ccn": 8,
        "bu14": bu14,
        "t": t or ts13,
        "fp": fp,
    }
    seg8 = encode_seg8(plain)
    seg10 = rev4(custom_b64_encode(rev3(b"appid,body,functionId" + b"\x03" * 3)))
    return ";".join([d, fp, app_id, token, seg5, "5.3", str(ts13), seg8, seg9, seg10])


def _body(mid):
    return {"funName": "getSkuByMaterialId", "page": {"pageNo": 1, "pageSize": 3},
            "param": {"materialId": mid, "requestScene": 0,
                      "requestExtFields": ["shopInfo"]}}


_COMMON = dict(
    function_id="unionSearchRecommend", appid="unionpc",
    fp="sanitizedfp00001", token="tk00" + "A" * 88, app_id="586ae",
    rd="zfUFWJ0sxS65", webgl_fp="0" * 32, canvas="0" * 32,
    bu14="EEmjRVVELq", salt5="AbCdEf7RvI<7|", salt9="GhIjKl9RvI<7|",
    random1="abcdefghijk", random2="lmnopqrstuv",
)

# (materialId, ts13, ts19, 期望 h5st) — 由 SDK 已验证的算法在固定参数下生成
SAMPLE_CASES = [
    (13884, 1788024996282, "20260830123456789",
     "20260830123456789;sanitizedfp00001;586ae;tk00AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA;85d09eab64434e5700c849f2fc3f8108d847dab409ea5d797954c0896afaf21b;5.3;1788024996282;q3EpJnof7rof7SlSGCUR3GFQKeEjLDIj7SFjLrJp-jod5TYdybIf7Lod0nojxjpOJrpjh7Jj66XaVSGXB2Vamipjxjpe6XETJrpjh7pdLDIj9e1TJrpjh7Jj7rof7rof7rof7rof7rof7rof7rof7rof7rof7rof7rIjLDIj7SnQEiVS0ipjLDrgJrof7rof7rof7rof7rof7rof7rof7rof7rof7rof7rofJrJdJfUT1yVTIipjLDrgJrIjLDIj3XETJrpjh7Jj3z5f9XIOMWlQCS1U2LFjLDIj1ipjLDrgJTUO3eEP6q0Q92lQJrJdJ31QHyVT5ipjLDrgJj4f9G1WJrJdJTlPJrpjh7ZMLrJpJHEaJrJdJfYf2iFjLrpjLDrg4rJdJnYf2iFjLrpjLDrg3nojxjpf6XETJrpjLrJp-LYgLDIj5nYOJipjLrpjh7JjACVRDOFSGa1TJmFjLDIj_ulS9mFPJrpjLrJp-bojxjpd2iFjLrpjLDrg6rJdJPYOJipjLrpjh7Zf_rJdJTYOJipjLrpjh7pfLDIj2XETJrpjLrJp-rojxjpe2iFjLrpjLDrg63pjxj5f2iFjLrpjLDrgJXIg6zpfJrJdJnYOJipjLrpjh7pe1rJdJ-1OJrpjLrJp-Xojxj5P-ipjLrpjh7pfLDIj-ipjLrpjh7pfLDIjHOEjLrpjLD7NLDIjHyVS3KUSJrpjh7ZMwqJdJrkPJrpjh7Jj3ToNL-oe1zVRUq5d7zpf6rpWdq5P0ulS9G1WJrJdJnVO4ipjLD7N;dea3fa1f315aeb10a1c872f3cce4e14cad239d50f231ab50b74d796b73d4fc14;of7rHGHQ8GlOIyVOF6ZNHuFT-bVR7qUT"),
    (10086, 1788025000282, "20260830123500789",
     "20260830123500789;sanitizedfp00001;586ae;tk00AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA;ba51bdd22fc697873b364a1a7a4656a70dac140d6f946f31b0c41d318f859508;5.3;1788025000282;q3EpJnof7rof7SlSGCUR3GFQKeEjLDIj7SFjLrJp-jod5rof7XIf7Lod0nojxjpOJrpjh7Jj66XaVSGXB2Vamipjxjpe6XETJrpjh7pdLDIj9e1TJrpjh7Jj7rof7rof7rof7rof7rof7rof7rof7rof7rof7rof7rIjLDIj7SnQEiVS0ipjLDrgJrof7rof7rof7rof7rof7rof7rof7rof7rof7rof7rofJrJdJfUT1yVTIipjLDrgJrIjLDIj3XETJrpjh7Jj3z5f9XIOMWlQCS1U2LFjLDIj1ipjLDrgJTUO3eEP6q0Q92lQJrJdJ31QHyVT5ipjLDrgJj4f9G1WJrJdJTlPJrpjh7ZMLrJpJHEaJrJdJfYf2iFjLrpjLDrg4rJdJnYf2iFjLrpjLDrg3nojxjpf6XETJrpjLrJp-LYgLDIj5nYOJipjLrpjh7JjACVRDOFSGa1TJmFjLDIj_ulS9mFPJrpjLrJp-bojxjpd2iFjLrpjLDrg6rJdJPYOJipjLrpjh7Zf_rJdJTYOJipjLrpjh7pfLDIj2XETJrpjLrJp-rojxjpe2iFjLrpjLDrg63pjxj5f2iFjLrpjLDrgJXIg6zpfJrJdJnYOJipjLrpjh7pe1rJdJ-1OJrpjLrJp-Xojxj5P-ipjLrpjh7pfLDIj-ipjLrpjh7pfLDIjHOEjLrpjLD7NLDIjHyVS3KUSJrpjh7ZMwqJdJrkPJrpjh7Jj3ToNL-oe1zVRUq5d7zpf6rpWdq5P0ulS9G1WJrJdJnVO4ipjLD7N;957b682c773eeaf712db338eacaa33f521d80106218b3c901cd75f01e48b1439;of7rHGHQ8GlOIyVOF6ZNHuFT-bVR7qUT"),
    (2024, 1788025016282, "20260830123655789",
     "20260830123655789;sanitizedfp00001;586ae;tk00AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA;0b72d73332e87c1120b5d30d1c1fa5fab7247775cdf4618973baf2fc83c78db5;5.3;1788025016282;q3EpJnof7rof7SlSGCUR3GFQKeEjLDIj7SFjLrJp-jod5TYf7XIf7Lod0nojxjpOJrpjh7Jj66XaVSGXB2Vamipjxjpe6XETJrpjh7pdLDIj9e1TJrpjh7Jj7rof7rof7rof7rof7rof7rof7rof7rof7rof7rof7rIjLDIj7SnQEiVS0ipjLDrgJrof7rof7rof7rof7rof7rof7rof7rof7rof7rof7rofJrJdJfUT1yVTIipjLDrgJrIjLDIj3XETJrpjh7Jj3z5f9XIOMWlQCS1U2LFjLDIj1ipjLDrgJTUO3eEP6q0Q92lQJrJdJ31QHyVT5ipjLDrgJj4f9G1WJrJdJTlPJrpjh7ZMLrJpJHEaJrJdJfYf2iFjLrpjLDrg4rJdJnYf2iFjLrpjLDrg3nojxjpf6XETJrpjLrJp-LYgLDIj5nYOJipjLrpjh7JjACVRDOFSGa1TJmFjLDIj_ulS9mFPJrpjLrJp-bojxjpd2iFjLrpjLDrg6rJdJPYOJipjLrpjh7Zf_rJdJTYOJipjLrpjh7pfLDIj2XETJrpjLrJp-rojxjpe2iFjLrpjLDrg63pjxj5f2iFjLrpjLDrgJXIg6zpfJrJdJnYOJipjLrpjh7pe1rJdJ-1OJrpjLrJp-Xojxj5P-ipjLrpjh7pfLDIj-ipjLrpjh7pfLDIjHOEjLrpjLD7NLDIjHyVS3KUSJrpjh7ZMwqJdJrkPJrpjh7Jj3ToNL-oe1zVRUq5d7zpf6rpWdq5P0ulS9G1WJrJdJnVO4ipjLD7N;538f3cb757e6f3ec0732b11157dea66ca26b5acb09a28af8c067f1ac8fa61e31;of7rHGHQ8GlOIyVOF6ZNHuFT-bVR7qUT"),
]


def main():
    passed = 0
    for mid, ts13, ts19, expected in SAMPLE_CASES:
        got = gen_h5st(body=_body(mid), ts13=ts13, ts19=ts19, t=ts13, **_COMMON)
        parts = got.split(";")
        lens = [len(x) for x in parts]
        ok = (got == expected and lens == [17, 16, 5, 92, 64, 3, 13, 788, 64, 32]
              and parts[9] == SEG10_CONST)
        env = decode_seg8(parts[7])
        ok = ok and env["fp"] == "sanitizedfp00001" and env["t"] == ts13
        passed += ok
        print("[%s] materialId=%d ts13=%d len=%d seg10=%s"
              % ("PASS" if ok else "FAIL", mid, ts13, len(got), parts[9][:12]))
        print("       seg8.fp=%s seg8.v=%s seg8.t=%d"
              % (env["fp"], env["v"], env["t"]))
        if not ok:
            print("       expected len=%d" % len(expected))
    print("\n%d/%d 通过" % (passed, len(SAMPLE_CASES)))
    if passed != len(SAMPLE_CASES):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
