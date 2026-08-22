/**
 * 米画师确定性验证 (交叉验证用)
 * 用法: node verify_fixed.js <url_path> [timestamp]
 * 强制 getRandomValues 返回全 0x42 -> 签名确定性 (浏览器 vs Node 字节一致,
 * 原项目已用同法验证 MATCH: true); 低熵签名会被服务端拒绝, 仅用于算法验证。
 */
const { createSigner } = require('./run_sign.js');

// 必须在 createSigner() 之前覆盖 (ensureCrypto 只补缺失项)
globalThis.crypto.getRandomValues = function (buf) {
    buf.fill(0x42);
    return buf;
};

const url = process.argv[2] || '/api/v1/artworks/search';
const ts = parseInt(process.argv[3]) || Math.floor(Date.now() / 1000);

createSigner().then(signer => {
    const sig = signer.sign(url, ts);
    process.stdout.write(JSON.stringify({ url, signature: sig, timestamp: ts }) + '\n');
    signer.free();
}).catch(err => {
    console.error(JSON.stringify({ error: err.message }));
    process.exit(1);
});
