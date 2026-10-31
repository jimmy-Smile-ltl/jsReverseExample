"use strict";

/**
 * 确定性签名运行器：固定 Math.random 序列 + 固定 Date，用于与 Python 侧逐字节对拍。
 *
 * 用法:
 *   node reference/node_deterministic.js <wafToken> <serverTs> <api> <method> \
 *        <nowMs> <seqA> <seqB> <seqMod> [seqLen]
 *
 * 序列 = ((i * seqA + seqB) % seqMod) / seqMod，与 main.py 的 _seq() 一致。
 * 输出 JSON: { token, randomCalls, nowMs, seq }。
 */

const path = require("path");
const XQW = require(path.join(__dirname, "..", "md1038_generator.js"));

const [wafToken, serverTs, api, method, nowRaw, aRaw, bRaw, mRaw, nRaw] =
  process.argv.slice(2);

if (!wafToken || !nowRaw) {
  console.error("usage: node reference/node_deterministic.js <wafToken> <serverTs> <api> <method> <nowMs> <a> <b> <m> [n]");
  process.exit(2);
}

const nowMs = Number(nowRaw);
const a = Number(aRaw), b = Number(bRaw), m = Number(mRaw);
const n = Number(nRaw || 48);
const seq = Array.from({ length: n }, (_, i) => ((i * a + b) % m) / m);

// 在调用签名函数前覆盖全局随机源与时间源
let calls = 0;
Math.random = () => seq[calls++ % seq.length];

const RealDate = Date;
global.Date = class extends RealDate {
  constructor(...args) {
    if (args.length) super(...args);
    else super(nowMs);
  }
  static now() { return nowMs; }
};

const token = XQW.md5_1038(wafToken, serverTs, { api, method, salt: "222029ad07" });
console.log(JSON.stringify({ token, randomCalls: calls, nowMs, seq }));
