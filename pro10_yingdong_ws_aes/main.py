"""
颍东先锋网 (www.ydxf.gov.cn) — 网盟 WEB_ISOLATION WAF: AES 会话加密 + WebSocket 指令渲染

用法:
    python main.py            # 运行全部样例验证 (无需网络)

原理 (app.3b14cce1.js webpack bundle):
    防护三层: 资源加密前缀 -> Session AES 加密 -> WSS 指令渲染 (msgpack/JSON)
    1. 固定密钥: AES-128-CBC key "0A234C4C639E015D" iv "E08247708934F42E",
       base64 输出把 '/' 换成 '_' (dynamicEncrypt / dynamicDecrypt)
    2. 会话密钥派生 (genrandomString + hasKey):
         e = 随机串 + 时间戳
         enc1 = AES(e, 固定密钥) 去掉 '_'  ->  session_key = enc1[1:17]  (作为 etag 头发送)
         enc2 = AES(session_key, 固定密钥)  ->  priKey      = enc2[4:20]
         session 请求体 = AES(JSON, priKey, session_key)   (注意参数顺序: key=priKey, iv=session_key)
    3. WebSocket: wss://{域名}/{前缀}/pr/{token}/{b|c}/ws/{tabId}/{uuid}
       帧格式 [seqNum, payload] / [[wrapper, [target, extra, command, ...args]]]
       CommandCodes: 31=NAVIGATE 32=SYNC 58=SIMPLE_HTML 等 (本复现带完整表)

样例来源: 密钥派生期望值 2026-06-29 抓包推导; SYNC 帧为真实观察消息 (ANALYSIS_REPORT 5.3)
"""

import base64
import json

from Crypto.Cipher import AES  # pip install pycryptodome
from Crypto.Util.Padding import pad, unpad

FIXED_KEY = "0A234C4C639E015D"   # 固定密钥 (16 字节 UTF-8)
FIXED_IV = "E08247708934F42E"    # 固定 IV (16 字节 UTF-8)

# CommandCodes 指令表 (自 app.js 提取, 服务端推送指令码)
COMMAND_CODES = {
    "TAB_OPS": 0, "DOM_EVENT": 4, "DOM_METHOD": 5, "RESET_DOM": 6,
    "ADD_DOC_TYPE": 7, "ADD_HTML_ELEMENT": 8, "ADD_SVG_ELEMENT": 9,
    "ADD_NS_ELEMENT": 10, "MOVE_ELEMENT": 11, "SHUFFLE_CHILDREN": 12,
    "EDIT_ELEMENT": 13, "DELETE_ELEMENT": 14, "ADD_STYLE": 15,
    "ADD_TEXT": 16, "MODIFY_TEXT": 17, "MODIFY_PROPERTY": 18,
    "MODIFY_ATTRIBUTES": 19, "SET_SELECTIONS": 20, "INSERT_RULE": 21,
    "DELETE_RULE": 22, "SET_CANVAS_DATA": 23, "DISABLED_STYLE": 24,
    "REPLACE_SYNC": 25, "WEBRTC": 30, "NAVIGATE": 31, "SYNC": 32,
    "SYNC_COOKIE": 34, "FILE": 35, "TAB_ACTIVE": 42, "NATIVE_METHOD": 44,
    "MODIFY_DOC_TYPE": 47, "CHANGE_BLOCK": 48, "RELOAD": 49,
    "SYNC_ALL_COOKIE": 50, "SYNC_WRITE_COOKIE": 51, "MEDIA_STATE": 52,
    "DOM_READY": 53, "AUGMENT_CSS": 54, "MULTI_CMD": 55,
    "REDIRECT_REQUEST": 56, "TEXTAREA_RESIZE": 57, "SIMPLE_HTML": 58,
    "RENDER_STATE": 59, "SYNC_CONFIG_TO_CLIENT_WIC": 60,
    "SYNC_CONFIG_TO_CLIENT_AIC": 61, "SYNC_CONFIG_TO_CLIENT_EIC": 62,
    "FRAME_PUSH_STATE": 63,
}


def dynamic_encrypt(plaintext: str, key: str = FIXED_KEY, iv: str = FIXED_IV) -> str:
    """AES-128-CBC -> base64, '/' 替换为 '_' (对应 JS dynamicEncrypt)"""
    cipher = AES.new(key.encode("utf-8"), AES.MODE_CBC, iv.encode("utf-8"))
    ct = cipher.encrypt(pad(plaintext.encode("utf-8"), AES.block_size))
    return base64.b64encode(ct).decode("ascii").replace("/", "_")


def dynamic_decrypt(ciphertext: str, key: str = FIXED_KEY, iv: str = FIXED_IV) -> str:
    """'_' 还原为 '/' -> base64 -> AES-128-CBC 解密 (对应 JS dynamicDecrypt)"""
    cipher = AES.new(key.encode("utf-8"), AES.MODE_CBC, iv.encode("utf-8"))
    ct = base64.b64decode(ciphertext.replace("_", "/"))
    return unpad(cipher.decrypt(ct), AES.block_size).decode("utf-8")


def derive_session_keys(random_e: str) -> tuple[str, str]:
    """会话密钥派生 -> (session_key/etag, priKey)

    对应 JS genrandomString + hasKey:
        enc1 = dynamicEncrypt(e).replace('_', '')  -> session_key = enc1[1:17]
        enc2 = dynamicEncrypt(session_key)         -> priKey      = enc2[4:20]
    """
    enc1 = dynamic_encrypt(random_e).replace("_", "")
    session_key = enc1[1:17]
    enc2 = dynamic_encrypt(session_key)
    pri_key = enc2[4:20]
    return session_key, pri_key


def encrypt_session(plaintext: str, session_key: str, pri_key: str) -> str:
    """session 请求体加密: AES(priKey, session_key) (对应 JS encryptSessions)"""
    return dynamic_encrypt(plaintext, key=pri_key, iv=session_key)


def decrypt_session(ciphertext: str, session_key: str, pri_key: str) -> str:
    """session 响应解密"""
    return dynamic_decrypt(ciphertext, key=pri_key, iv=session_key)


def build_ws_frame(seq_num: int, payload: list) -> str:
    """客户端发送帧 (文本模式): [seqNum, payload]"""
    return json.dumps([seq_num, payload], ensure_ascii=False, separators=(",", ":"))


def parse_ws_frame(frame: str) -> list:
    """解析服务端帧: [[wrapper, [target, extra, command, ...args]]]"""
    return json.loads(frame)


# ============================================================ 样例验证

def main() -> None:
    passed = 0
    total = 0

    def check(ok: bool, label: str, detail: str = "") -> None:
        nonlocal passed, total
        total += 1
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label} {detail}")

    # 1. 固定密钥派生期望值 (2026-06-29 抓包推导, 固定输入)
    e = "8k3m2x9p-7q1z4f6a1754123456789"
    session_key, pri_key = derive_session_keys(e)
    check(session_key == "QCoJiAwUS8cCUled", "derive session_key/etag", f"({session_key})")
    check(pri_key == "64c8jDPjVvcoYK38", "derive priKey", f"({pri_key})")

    # 2. base64 '/'->'_' 变形往返
    enc = dynamic_encrypt("hello 颍东先锋网")
    check("_" in enc and "/" not in enc and dynamic_decrypt(enc) == "hello 颍东先锋网",
          "base64 slash transform", f"(len {len(enc)})")

    # 3. session 请求体加密往返 (真实数据结构, 中文)
    session_data = {
        "uuid": "cedef036-cc2e-4a1d-99a3-8f6d3c2b1a90",
        "url": "https://www.ydxf.gov.cn/News/showList/1/page_1.html",
        "cid": "m1r1cvj2",
        "_": "Mozilla/5.0 (Windows NT 10.0) Chrome/131.0.0.0|m1r1cvj2",
        "common": {"userAgent": "Mozilla/5.0", "platform": "Win32",
                   "language": "zh-CN", "languages": "zh-CN,zh;q=0.9,en;q=0.8"},
        "extension": {"reuse": False, "simMode": False},
    }
    enc_body = encrypt_session(json.dumps(session_data, ensure_ascii=False), session_key, pri_key)
    restored = json.loads(decrypt_session(enc_body, session_key, pri_key))
    check(restored == session_data, "session roundtrip", f"(b64 len {len(enc_body)})")

    # 4. 派生密钥确定性: 同 e 两次派生一致
    check(derive_session_keys(e) == derive_session_keys(e), "derivation deterministic")

    # 5. WebSocket 帧: NAVIGATE 发送帧可解析 + 真实 SYNC 帧结构 (2026-06-29 观察)
    frame = build_ws_frame(31, [-1, ["/News/showList/2/page_1.html", "_self", False]])
    parsed = parse_ws_frame(frame)
    check(parsed == [31, [-1, ["/News/showList/2/page_1.html", "_self", False]]],
          "WS navigate frame", f"(len {len(frame)})")
    sync = parse_ws_frame("[[-1, [\"\", \"\", 32, 1, false]]]")  # 真实观察消息
    check(sync == [[-1, ["", "", 32, 1, False]]] and sync[0][1][2] == COMMAND_CODES["SYNC"],
          "WS sync frame (captured)", f"(command={sync[0][1][2]})")

    # 6. CommandCodes 表抽查
    check(COMMAND_CODES["NAVIGATE"] == 31 and COMMAND_CODES["SIMPLE_HTML"] == 58
          and COMMAND_CODES["ADD_HTML_ELEMENT"] == 8, "CommandCodes table",
          "(31 NAVIGATE / 58 SIMPLE_HTML / 8 ADD_HTML_ELEMENT)")

    print(f"\n{passed}/{total} passed")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
