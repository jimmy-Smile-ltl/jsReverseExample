"use strict";

var XQW = (function() {
    var _CHAR_TABLE = "g_GTtAIr2=sVcC6wvxopuSQYWbjFl5O3P7qeZakJBLiyXd8z/f4U09HmKRMhEDNn1";

    var _HEX = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F"];

    function sha1Encrypt(mA) {
        function rotateLeft(n, b) {
            return (n << b) | (n >>> (32 - b));
        }
        function toHexStr(n) {
            var s = "", v;
            for (var i = 7; i >= 0; i--) {
                v = (n >>> (i * 4)) & 0xf;
                s += v.toString(16);
            }
            return s;
        }
        var str = unescape(encodeURIComponent(mA));
        var blockStart, i;
        var W = new Array(80);
        var H0 = 0x67452301, H1 = 0xEFCDAB89, H2 = 0x98BADCFE, H3 = 0x10325476, H4 = 0xC3D2E1F0;
        var A, B, C, D, E, temp;
        var msg = str;
        var msg_len = msg.length;
        var word_array = [];
        for (i = 0; i < msg_len - 3; i += 4) {
            word_array.push(
                (msg.charCodeAt(i) & 0xff) << 24 |
                (msg.charCodeAt(i + 1) & 0xff) << 16 |
                (msg.charCodeAt(i + 2) & 0xff) << 8 |
                (msg.charCodeAt(i + 3) & 0xff)
            );
        }
        switch (msg_len % 4) {
            case 0:
                i = 0x80000000;
                break;
            case 1:
                word_array.push((msg.charCodeAt(msg_len - 1) & 0xff) << 24 | 0x800000);
                break;
            case 2:
                word_array.push((msg.charCodeAt(msg_len - 2) & 0xff) << 24 | (msg.charCodeAt(msg_len - 1) & 0xff) << 16 | 0x8000);
                break;
            case 3:
                word_array.push((msg.charCodeAt(msg_len - 3) & 0xff) << 24 | (msg.charCodeAt(msg_len - 2) & 0xff) << 16 | (msg.charCodeAt(msg_len - 1) & 0xff) << 8 | 0x80);
                break;
        }
        while ((word_array.length % 16) != 14) {
            word_array.push(0);
        }
        word_array.push(msg_len >>> 29);
        word_array.push((msg_len << 3) & 0xffffffff);
        for (blockStart = 0; blockStart < word_array.length; blockStart += 16) {
            for (i = 0; i < 16; i++) {
                W[i] = word_array[blockStart + i];
            }
            for (i = 16; i < 80; i++) {
                W[i] = rotateLeft(W[i - 3] ^ W[i - 8] ^ W[i - 14] ^ W[i - 16], 1);
            }
            A = H0; B = H1; C = H2; D = H3; E = H4;
            for (i = 0; i < 80; i++) {
                if (i < 20) {
                    temp = (rotateLeft(A, 5) + ((B & C) | (~B & D)) + E + W[i] + 0x5A827999) & 0xffffffff;
                } else if (i < 40) {
                    temp = (rotateLeft(A, 5) + (B ^ C ^ D) + E + W[i] + 0x6ED9EBA1) & 0xffffffff;
                } else if (i < 60) {
                    temp = (rotateLeft(A, 5) + ((B & C) | (B & D) | (C & D)) + E + W[i] + 0x8F1BBCDC) & 0xffffffff;
                } else {
                    temp = (rotateLeft(A, 5) + (B ^ C ^ D) + E + W[i] + 0xCA62C1D6) & 0xffffffff;
                }
                E = D; D = C; C = rotateLeft(B, 30); B = A; A = temp;
            }
            H0 = (H0 + A) & 0xffffffff;
            H1 = (H1 + B) & 0xffffffff;
            H2 = (H2 + C) & 0xffffffff;
            H3 = (H3 + D) & 0xffffffff;
            H4 = (H4 + E) & 0xffffffff;
        }
        return (toHexStr(H0) + toHexStr(H1) + toHexStr(H2) + toHexStr(H3) + toHexStr(H4)).toLowerCase();
    }

    function m2(mm) {
        var mQ = sha1Encrypt(mm);
        var mN = [];
        for (var mB = 10; mB < 26; ++mB) {
            mN.push(mQ[mB % mQ.length]);
        }
        return mN;
    }

    function m4(mm) {
        function q(mm) {
            var ml = "";
            for (var mX = 0; mX < mm.length; mX += 2) {
                var mN = parseInt(mm[mX] + mm[mX + 1], 16);
                var mB = _HEX[Math.floor(16 * 0.17851588055023077)] + _HEX[Math.floor(16 * Math.random())];
                var mQ = (mN ^ parseInt(mB, 16)).toString(16);
                if (mQ.length == 1) {
                    mQ = "0" + mQ;
                }
                ml += mQ;
            }
            return ml.split("");
        }
        return q(mm).join("").toLowerCase();
    }

    function F() {
        var mm = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
        mm.push(Math.random() > 0.5 ? 1 : 0);
        mm.push(1);
        mm.push(Math.floor(new Date().getTime() / 1000) % 2);
        mm.push(Math.random() > 0.5 ? 1 : 0);
        mm.push(0, 0, 0, 1, 0, 0, 0, 1);
        for (var i = mm.length - 1; i >= 0; i--) {
            var j = Math.floor(Math.random() * (i + 1));
            var tmp = mm[i]; mm[i] = mm[j]; mm[j] = tmp;
        }
        var result = 0;
        for (var i = 0; i < mm.length; i++) {
            result |= (mm[i] ? 1 : 0) << i;
        }
        return result;
    }

    function XR(p0, p1, p2) {
        var p3 = 0;
        var p4 = p1;
        var p5 = p0.length;
        var p6 = p2 || 1;
        while (p4 < p5) {
            p3 = (p3 << 5) - p3;
            p3 += p0.charCodeAt(p4);
            p3 >>>= 0;
            p4 += p6;
        }
        return p3;
    }

    function mc7Generator() {
        var Xx = new Date().getTime();
        var p1 = XR((4294967295 * Math.random() >>> 0) + "|" + Xx, 0, 1) + "a" + Xx.toString(16);
        return encodeURIComponent(p1);
    }

    function LZW(input) {
        var dict = {};
        var dictSize = 256 + _CHAR_TABLE.length;
        var nextCode = dictSize;
        var codeBits = 9;
        var codeCounter = Math.pow(2, codeBits);

        for (var i = 0; i < _CHAR_TABLE.length; i++) {
            dict[_CHAR_TABLE[i]] = i;
        }
        for (var i = 0; i < 256; i++) {
            var ch = String.fromCharCode(i);
            if (dict[ch] === undefined) {
                dict[ch] = _CHAR_TABLE.length + i;
            }
        }

        var w = "";
        var bitBuffer = 0;
        var bitCount = 0;
        var result = [];
        var bitsPerChar = 6;

        function flushCode(code) {
            for (var b = codeBits - 1; b >= 0; b--) {
                bitBuffer = (bitBuffer << 1) | ((code >>> b) & 1);
                bitCount++;
                if (bitCount === bitsPerChar) {
                    result.push(_CHAR_TABLE[bitBuffer]);
                    bitBuffer = 0;
                    bitCount = 0;
                }
            }
            if (--codeCounter <= 0) {
                codeBits++;
                codeCounter = Math.pow(2, codeBits);
            }
        }

        for (var i = 0; i < input.length; i++) {
            var c = input[i];
            var wc = w + c;
            if (dict.hasOwnProperty(wc)) {
                w = wc;
            } else {
                flushCode(dict[w]);
                dict[wc] = nextCode++;
                w = String(c);
            }
        }

        if (w !== "") {
            flushCode(dict[w]);
        }

        if (bitCount > 0) {
            bitBuffer = bitBuffer << (bitsPerChar - bitCount);
            result.push(_CHAR_TABLE[bitBuffer]);
            bitBuffer = 0;
            bitCount = 0;
        }

        return result.join("");
    }

    function buildFingerprint(opts) {
        opts = opts || {};
        var ua = opts.ua || "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36";
        var platform = opts.platform || "Win32";
        var sw = opts.screenWidth || 1920;
        var sh = opts.screenHeight || 1080;
        var colorDepth = opts.colorDepth || 24;
        return [
            ua, platform, sw, sh, sw, sh, colorDepth, 1,
            opts.hardwareConcurrency || 8,
            (opts.deviceMemory || 8).toString()
        ].join("###");
    }

    function md5_1038(wafToken, serverTimestamp, options) {
        options = options || {};
        var api = options.api || "xueqiu.com/statuses/fundx/public/list.json";
        var method = options.method || "get";
        var salt = options.salt || "222029ad07";
        var fingerprint = options.fingerprint || buildFingerprint(options);

        var mp = encodeURIComponent(wafToken + method + salt + api);
        var mu = mp + encodeURIComponent(fingerprint);

        var mc1 = m4(m2(mu));
        var mc2 = m4(m2(mp));
        var mc3 = F();
        var mc4 = new Date().getTime().toString();
        var mc7 = mc7Generator();

        var mc = [mc1, mc2, mc3, mc4, wafToken, serverTimestamp, mc7].join("|");
        return salt + "-" + LZW(mc);
    }

    return {
        sha1Encrypt: sha1Encrypt,
        m2: m2,
        m4: m4,
        F: F,
        XR: XR,
        mc7Generator: mc7Generator,
        LZW: LZW,
        buildFingerprint: buildFingerprint,
        md5_1038: md5_1038
    };

})();

if (typeof module !== "undefined" && module.exports) {
    module.exports = XQW;
}
