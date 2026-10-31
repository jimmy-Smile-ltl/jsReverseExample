// parity_harness.js — 确定性对拍 Node 端
// 用法: node parity_harness.js <inputs.json 路径>
// 读取 {seed, now, params, data, ua}, 注入 mulberry32 + 固定 Date.now,
// 加载 ../shared/sign_engine.js 原始快照执行 getABogus, stdout 输出 a_bogus
const fs = require('fs');
const path = require('path');

const cfg = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));

// 确定性 PRNG (mulberry32) — Python 端 Mulberry32 逐位一致
let a = (cfg.seed >>> 0) | 0;
global.Math.random = function () {
    a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
};

// 固定时间源
const FIXED = cfg.now;
global.Date.now = function () { return FIXED; };

// 加载同目录 sign_engine.js (不修改其源码)
const src = fs.readFileSync(path.join(__dirname, 'sign_engine.js'), 'utf8');
const mod = { exports: {} };
new Function('module', 'exports', 'require', src)(mod, mod.exports, require);
const { getABogus } = mod.exports;

const out = getABogus(cfg.params, cfg.data, cfg.ua);
console.log(out);
