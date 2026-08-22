/**
 * gdtv.cn 固定时间戳验证 (交叉验证用)
 * 用法: node verify_fixed.js [method] [url] [deviceId]
 * 固定 Date -> 排除时间变量 -> 可证明 URL/deviceId/method 是否参与签名;
 * 注意: 签名含时区偏移 (__wbg_getTimezoneOffset), 期望值随机器时区变化, 只做自洽对比.
 */
const { sign } = require('./signer.js');

// wbg 的 __wbg_getTime 可能以两种方式取时间, 两个都固定
const FIXED_TS = 1787153907256;
Date.prototype.getTime = function () { return FIXED_TS; };
Date.now = function () { return FIXED_TS; };
// 签名含时区偏移 (__wbg_getTimezoneOffset), 固定为 UTC+8 保证跨机器一致
Date.prototype.getTimezoneOffset = function () { return -480; };

const method = process.argv[2] || "GET";
const url = process.argv[3] || "https://gdtv-api.gdtv.cn/api/v1/seoConfig";
const deviceId = process.argv[4] || "WEB_nodejs_00000000-0000-0000-0000-000000000001";

const headers = sign(method, url, deviceId, "WEB_PC", "", undefined);
const output = {};
for (const [k, v] of Object.entries(headers)) {
    output[k.toLowerCase()] = String(v);
}
console.log(JSON.stringify(output));
