/**
 * 米画师 M-S 签名 — 一次性调用脚本
 * 用法: node sign.js <url1> [url2] ... [--ts=timestamp]
 * 输出: 每行一个 JSON {"url":"...", "signature":"...", "timestamp":123}
 *
 * 补环境: run_sign.js 内置所有浏览器 API stubs
 */
const { createSigner } = require('./run_sign.js');

const args = process.argv.slice(2);
let ts = Math.floor(Date.now() / 1000);
const urls = [];

for (const a of args) {
    if (a.startsWith('--ts=')) {
        ts = parseInt(a.slice(5)) || ts;
    } else {
        urls.push(a);
    }
}

if (urls.length === 0) {
    console.error('Usage: node sign.js <url_path> [url2...] [--ts=timestamp]');
    process.exit(1);
}

createSigner().then(signer => {
    for (const url of urls) {
        const sig = signer.sign(url, ts);
        process.stdout.write(JSON.stringify({ url, signature: sig, timestamp: ts }) + '\n');
    }
    signer.free();
}).catch(err => {
    console.error(JSON.stringify({ error: err.message }));
    process.exit(1);
});
