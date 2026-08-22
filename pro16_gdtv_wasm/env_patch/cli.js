/**
 * gdtv.cn WASM 签名器 CLI
 *
 * 用法:
 *   node cli.js [method] [url] [deviceId] [platform] [options]
 *
 * 示例:
 *   node cli.js
 *   node cli.js GET "https://gdtv-api.gdtv.cn/api/v1/seoConfig"
 *   node cli.js GET "https://gdtv-api.gdtv.cn/api/channel/v1/news?channelId=117&pageSize=5"
 */

const { sign, greet, getCaKey, wasmBinarySize } = require("./signer");

const args = process.argv.slice(2);
const method = args[0] || "GET";
const url = args[1] || "https://gdtv-api.gdtv.cn/api/v1/seoConfig";
const deviceId = args[2] || "WEB_nodejs_00000000-0000-0000-0000-000000000001";
const platform = args[3] || "WEB_PC";
const options = args[4] || "";

try {
    const headers = sign(method, url, deviceId, platform, options);

    // 确保所有值为字符串，key 转为小写 (Python 兼容)
    const output = {};
    for (const [k, v] of Object.entries(headers)) {
        output[k.toLowerCase()] = String(v);
    }

    console.log(JSON.stringify(output));
} catch (e) {
    console.error(JSON.stringify({ error: e.message }));
    process.exit(1);
}
