"""
中国社会组织政务服务平台 (xxgs.chinanpo.mca.gov.cn) — 滑块验证码 a/b/c 参数加密

用法:
    python main.py            # 运行样例验证 (无需网络, 无需 cv2)

原理:
    搜索接口 gridQuery 需要滑块验证通过的 a/b/c 三参数:
        1. GET /slideCaptcha -> {result: {a, b, c: {cutImage, oriImage}}}
           a/b 为服务端下发的随机串, cutImage/oriImage 为滑块缺口图与原图 (base64 PNG)
        2. 缺口识别 -> 移动距离 length (OpenCV matchTemplate, 见 find_gap)
        3. newA = base64(a)          # 仅再编码
           newB = base64(b)          # 仅再编码
           newC = base64(base64(RSA_1024_pkcs1v15(str(length))))  # 双重 base64
        4. GET /slide_captcha_check?a=newA&b=newB&c=newC -> code==200 即有效
    加密主体是 RSA 加密 + 双重 base64 嵌套, 无 JS 混淆。

样例来源: 2024-07 实战抓包 (baseInfoSpider.py + cutImage.txt/oriImage.txt 真实图片)
"""

import base64

from Crypto.Cipher import PKCS1_v1_5  # pip install pycryptodome
from Crypto.PublicKey import RSA

# 服务端 RSA 公钥 (1024-bit, PKCS#1 v1.5 填充), 自 /slideCaptcha 配套 JS 中提取
PUB_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCCsYUGHMhjSzdMqn9JzPfKs9Jb
xXTPtHofTv7reV0HrEz4brnE6ZJpNn5s934KO3L4QDF7ELHysIiounhhpF1bewW9
jKdcpZA5M1CkGHKcwpLA2liaqOlt/0Mf3ui9jxR9AHxUMFVGfJ6Q4+cEmDBUAEOX
lxqk4ZjGpubwGNk9XQIDAQAB
-----END PUBLIC KEY-----"""


def rsa_encrypt(content: str) -> str:
    """复现原项目 rsaEncrypt(): RSA 加密 -> base64 -> 再 base64 (双重嵌套)。

    原实现 (python rsa 库, PKCS1 v1.5 填充) 与 pycryptodome 的 PKCS1_v1_5
    完全兼容。注意 rsa 库的 rsa.encrypt 即 PKCS#1 v1.5, 密文固定 128 字节
    (1024-bit), 最终双重 base64 后固定 232 字符。
    """
    cipher = PKCS1_v1_5.new(RSA.import_key(PUB_KEY_PEM))
    crypto = cipher.encrypt(content.encode())
    return base64.b64encode(base64.b64encode(crypto)).decode()


def build_abc(a: str, b: str, distance: int) -> tuple[str, str, str]:
    """完整 a/b/c 生成: (newA, newB, newC)"""
    new_a = base64.b64encode(a.encode()).decode()
    new_b = base64.b64encode(b.encode()).decode()
    new_c = rsa_encrypt(str(distance))
    return new_a, new_b, new_c


def decode_new_c(new_c: str) -> tuple[str, bytes]:
    """c 的解码链验证: 第一层 base64 串 -> 第二层 128 字节 RSA 密文"""
    layer1 = base64.b64decode(new_c).decode()
    return layer1, base64.b64decode(layer1)


def find_gap(cut_image_b64: str, ori_image_b64: str) -> int:
    """可选: 滑块缺口识别 -> 移动距离 (像素)。

    依赖 opencv-python (pip install opencv-python), 不安装也能跑其余验证。
    方法: 原图转灰度, matchTemplate(TM_CCOEFF_NORMED) 模板匹配缺口小图,
    返回最佳匹配的 x 坐标。原项目用 requests_html+retry 包装, 多次尝试保证通过。
    """
    import cv2
    import numpy as np

    cut = cv2.imdecode(np.frombuffer(base64.b64decode(cut_image_b64), np.uint8), 0)
    ori = cv2.imdecode(np.frombuffer(base64.b64decode(ori_image_b64), np.uint8), 0)
    result = cv2.matchTemplate(ori, cut, cv2.TM_CCOEFF_NORMED)
    _, _, _, max_loc = cv2.minMaxLoc(result)
    return int(max_loc[0])


# ------------------------------------------------------------------ 样例验证

def main() -> None:
    passed = 0
    total = 0

    # 1. a/b 编码可逆验证 (a/b 为服务端每次下发的随机串, 未留存历史值;
    #    base64 编码可逆, 以 b64decode(b64encode(x)) == x 验证编码正确性)
    for raw in ["ABCdef123", "9f8e7d6c-5b4a-3c2d-1e0f-abcdef123456",
                "x" * 30 + "=="]:
        total += 1
        ok = base64.b64decode(base64.b64encode(raw.encode())).decode() == raw
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] a/b base64 roundtrip {raw[:12]!r}...")

    # 2. RSA 密文结构验证: 双重 base64 链长度固定 232 字符, 内层 128 字节
    for dist in [123, 246, 0]:
        total += 1
        new_c = rsa_encrypt(str(dist))
        layer1, ciphertext = decode_new_c(new_c)
        ok = (len(new_c) == 232 and len(layer1) == 172 and len(ciphertext) == 128)
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] rsa_encrypt({dist}) len={len(new_c)} "
              f"(expect 232/172/128)")

    # 3. RSA 随机填充性质: 相同输入两次加密密文不同, 但长度恒定
    total += 1
    c1 = rsa_encrypt("246")
    c2 = rsa_encrypt("246")
    ok = c1 != c2 and len(c1) == len(c2)
    passed += ok
    print(f"[{'PASS' if ok else 'FAIL'}] RSA randomized (c1 != c2, same len)")

    # 4. 真实抓包图片数据: cutImage.txt/oriImage.txt 为合法 PNG (2024-07 抓包)
    import os
    data_dir = os.path.dirname(os.path.abspath(__file__))
    for name in ["cutImage.txt", "oriImage.txt"]:
        total += 1
        with open(os.path.join(data_dir, name), "rb") as f:
            img = base64.b64decode(f.read())
        ok = img[:4] == b"\x89PNG"
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {name} is valid PNG ({len(img)} bytes)")

    # 5. 可选: 缺口识别 (需要 opencv-python)
    total += 1
    try:
        with open(os.path.join(data_dir, "cutImage.txt"), "rb") as f:
            cut_b64 = f.read().decode()
        with open(os.path.join(data_dir, "oriImage.txt"), "rb") as f:
            ori_b64 = f.read().decode()
        gap = find_gap(cut_b64, ori_b64)
        ok = gap > 0
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] find_gap -> distance={gap}px")
    except ImportError:
        print("[SKIP] find_gap: opencv-python 未安装 (pip install opencv-python)")
        total -= 1

    print(f"\n{passed}/{total} passed")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
