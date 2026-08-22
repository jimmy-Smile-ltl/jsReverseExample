/**
 * 酷狗 RSA-1024 NoPadding 独立实现 (交叉验证用)
 * 用法: node rsa_ref.js <aes_key> <clienttime_ms>
 * 逻辑与 kugou_encrypt.js 一致: payload 反转 + 前导零 + little-endian + modpow
 */
const MOD = 'B1B1EC76A1BBDBF0D18E8CD9A87E53FA3881E2F004C67C9DDA2CA677DBEFA3D61DF8463FE12D84FF4B4699E02C9D41CAB917F5A8FB9E35580C4BDF97763A0420A476295D763EE10174E6F9EBF7DF8A77BA5B20CDA4EE705DEF5BBA3C88567B9656E52C9CD5CD95CA735FF2D25F762B133273EEEB7B4F3EA8B6DA29040F3B67CD';
const E = 0x10001n;

const payload = JSON.stringify({ clienttime_ms: parseInt(process.argv[3]), key: process.argv[2] });
const pb = Buffer.from(payload, 'utf8');
const ba = Buffer.alloc(128);
for (let i = 0; i < pb.length; i++) ba[128 - pb.length + i] = pb[pb.length - 1 - i];

let m = 0n;
for (let i = 0; i < 128; i++) m |= BigInt(ba[i]) << BigInt(8 * i);

let r = 1n, b = m % BigInt('0x' + MOD), e = E;
while (e > 0n) { if (e & 1n) r = (r * b) % BigInt('0x' + MOD); e >>= 1n; b = (b * b) % BigInt('0x' + MOD); }
console.log(r.toString(16).padStart(256, '0'));
