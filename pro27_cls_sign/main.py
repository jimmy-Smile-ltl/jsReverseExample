"""
pro27 财联社电报 sign — SHA1→MD5 双重哈希签名

复现 cls.cn 电报接口的 sign 参数生成算法 (纯标准库, 无第三方依赖):

    sign = MD5( SHA1( query_string ).hexdigest() ).hexdigest()   # 32 位小写 hex

其中 query_string 由请求参数递归序列化而来:
    1. key 按大写形式排序 (不区分大小写)
    2. 嵌套 dict/list 展开为 key[nested][idx]=value, 嵌套层同样排序
    3. bool 序列化为 true/false, None 跳过, 空数组 → key[]
    4. 用 & 连接所有键值对

来源: 财联社 webpack bundle _app.js 的 module 36498 (sign 函数),
     SHA1 为 Rusha 实现, MD5 标准。JS→Python 差异:
     排序键为 k.toUpperCase() 对应 Python sorted(key=str.upper)。

用法:
    python main.py            # 运行 5 组内置抓包样例, 输出即验证

样例来源: 2026-06 财联社 telegraph/telegraphList 接口抓包
(原项目: spider research/其他/pro10 财联社/rpc/sign.py, 已实测 5/5 通过)
"""

import hashlib

# ---------------------------------------------------------------- 核心复现
def _serialize(key: str, value) -> str:
    """递归序列化参数为 key=value 片段 (对齐 JS sign 模块的序列化逻辑)。

    - None → 跳过 (返回 None)
    - bool → "key=true/false" (小写)
    - str/int/float → "key=value"
    - list → "key[0]=v0&key[1]=v1..." (空数组 → "key[]")
    - dict → 按 key 大写排序展开 "key[nested]=value"
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return "{}={}".format(key, str(value).lower())
    if isinstance(value, (str, int, float)):
        return "{}={}".format(key, value)
    if isinstance(value, list):
        if not value:
            return "{}[]".format(key)
        parts = []
        for i, v in enumerate(value):
            r = _serialize("{}[{}]".format(key, i), v)
            if r is not None:
                parts.append(r)
        return "&".join(parts) if parts else None
    if isinstance(value, dict):
        sub_keys = sorted(value.keys(), key=lambda k: k.upper())
        parts = []
        for k in sub_keys:
            r = _serialize("{}[{}]".format(key, k), value[k])
            if r is not None:
                parts.append(r)
        return "&".join(parts) if parts else None
    return "{}={}".format(key, value)


def compute_sign(params: dict) -> tuple:
    """计算 sign = MD5(SHA1(query_string).hexdigest()).hexdigest()

    返回 (sign, query_string, sha1_hex) 便于调试中间值。
    """
    # 1. key 排序: JS 用 k.toUpperCase() 比较 → Python key=str.upper
    sorted_keys = sorted(params.keys(), key=lambda k: k.upper())
    # 2~3. 序列化 + & 连接
    parts = [r for k in sorted_keys if (r := _serialize(k, params[k]))]
    query_string = "&".join(parts)
    # 4. SHA1 → hex (JS Rusha 输出 40 位小写 hex)
    sha1_hash = hashlib.sha1(query_string.encode()).hexdigest()
    # 5. MD5(SHA1_hex) → 32 位小写 hex
    sign = hashlib.md5(sha1_hash.encode()).hexdigest()
    return sign, query_string, sha1_hash


def get_sign(params: dict) -> str:
    """简化接口: 只返回 sign"""
    return compute_sign(params)[0]


# ---------------------------------------------------------------- 样例验证
# (params, 期望 sign) — 5 组取自 2026-06 财联社接口抓包
SAMPLE_CASES = [
    ({"app": "CailianpressWeb", "os": "web", "sv": "8.7.9"},
     "b02d8f7bc4c45eeb3e86904203597da2"),
    ({"app": "CailianpressWeb", "name": "telegraph", "os": "web", "sv": "8.7.9"},
     "6c73b056a64891cdc257dcf1914464ad"),
    ({"app": "CailianpressWeb", "lastTime": "1780569021", "name": "telegraphList",
      "os": "web", "sv": "8.7.9"},
     "08c4bd752e9f95afbbec3283a6564cf6"),
    ({"app": "CailianpressWeb", "fields": "secu_name,secu_code,trade_status,change,change_px,last_px",
      "os": "web", "secu_codes": "sh000001,sz399001,sh000905,sz399006", "sv": "8.7.9"},
     "9e0b2a4b062fadc82407b8b50982a164"),
    ({"app": "CailianpressWeb", "os": "web", "rever": "1", "sv": "8.7.9",
      "type": "industry", "way": "change"},
     "00231877ba09a2a8b50daa83c7422b48"),
]


def main() -> None:
    passed = 0
    for params, expected in SAMPLE_CASES:
        sign, qs, sha1 = compute_sign(params)
        ok = sign == expected
        passed += ok
        print("[%s] sign=%s" % ("PASS" if ok else "FAIL", sign))
        print("      qs=%s" % qs)
        if not ok:
            print("      expected: %s" % expected)
    print("\n%d/%d 通过" % (passed, len(SAMPLE_CASES)))
    if passed != len(SAMPLE_CASES):
        raise SystemExit(1)


# ---------------------------------------------------------------- 可选: 真实请求验证
# 真实请求 (需网络, 不进入 main 流程):
#   GET https://www.cls.cn/nodeapi/telegraphList?app=CailianpressWeb&lastTime=...&os=web&sv=8.7.9&sign=<计算值>
# 抓包步骤: F12 → Network → 过滤 nodeapi → 复制参数 → 对照本脚本计算 sign

if __name__ == "__main__":
    main()
