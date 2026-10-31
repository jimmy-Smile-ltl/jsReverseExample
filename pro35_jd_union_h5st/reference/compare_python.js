/**
 * 参考脚本：Python 纯算法 vs SDK 补环境 同 run 逐段对比（2026-08-30）
 * 注意：依赖同目录 sign.js（京东联盟 SDK，未随仓库分发）与 Node 环境；
 *       仅保留「同 run 注入 + 逐段 diff」的方法代码，不能直接运行。
 */
/**
 * compare_python.js — Python 纯算法 vs SDK 补环境 同 run 逐段对比
 *
 * 1. hook sign.js 捕获全部动态参数 + 参考 h5st
 * 2. 参数写 JSON → 调 py -3.12 h5st_pure.py 生成
 * 3. 逐段对比
 */
const origCall = Function.prototype.call;
const _B = globalThis.Buffer;
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
let hookedCall;
let X = null, ts19 = null, rd = null;
const parseInputs = [];
function isWA(v) { return v && typeof v === 'object' && Array.isArray(v.words) && typeof v.sigBytes === 'number'; }
hookedCall = function (thisArg, ...args) {
    const fn = this;
    if (fn === hookedCall) return origCall.apply(fn, arguments);
    const fnName = (fn && fn.name) || 'anon';
    const r = origCall.apply(fn, arguments);
    if (fnName === 'test' && !X) { rd = fn.toString().match(/rd='([^']+)'/)[1]; ts19 = args[2]; X = r; }
    if (X && fnName === 'parse') {
        for (const a of args) {
            if (typeof a === 'string' && a.length > 100 && a.indexOf(X) === 0) parseInputs.push(a);
        }
    }
    return r;
};
Function.prototype.call = hookedCall;

const { sign } = require('./sign.js');

const MAP1 = 'rqponmlkjihgfedcbaZYXWVUTSRQPONMLKJIHGFEDCBA-_9876543210zyxwvuts';
const R = {}; for (let i = 0; i < MAP1.length; i++) R[MAP1[i]] = i;
function decSeg8(seg) {
    let b64 = ''; for (let i = 0; i < seg.length; i += 4) b64 += seg.substring(i, i + 4).split('').reverse().join('');
    const bytes = [];
    for (let i = 0; i < b64.length; i += 4) {
        const n = (R[b64[i]] << 18) | (R[b64[i + 1]] << 12) | (R[b64[i + 2]] << 6) | R[b64[i + 3]];
        bytes.push((n >> 16) & 255, (n >> 8) & 255, n & 255);
    }
    let buf = _B.from(bytes);
    const blocks = []; for (let i = 0; i < buf.length; i += 3) blocks.push(buf.slice(i, i + 3));
    return _B.concat(blocks.reverse());
}

(async function () {
    const input = { functionId: 'unionSearchRecommend', appid: 'unionpc', body: { funName: 'getSkuByMaterialId', page: { pageNo: 1, pageSize: 3 }, param: { materialId: 13884, requestScene: 0, requestExtFields: ['shopInfo'] } } };
    const h5st = await sign(input);
    const ref = h5st.split(';');
    const salt5 = parseInputs[0].substring(parseInputs[0].length - 12);
    const salt9 = parseInputs[1].substring(parseInputs[1].length - 12);
    const refJson = decSeg8(ref[7]).toString('utf8');
    const rnd = refJson.match(/"random": "([^"]+)"/g).map(s => s.match(/"([^"]+)"$/)[1]);
    const t = Number(refJson.match(/"t": (\d+)/)[1]);

    const params = {
        functionId: input.functionId, appid: input.appid,
        body_json: JSON.stringify(input.body),
        fp: ref[1], token: ref[3], appId: ref[2],
        rd, ts19, date: ref[0], ts13: Number(ref[6]), t,
        salt5, salt9, random1: rnd[0], random2: rnd[1],
    };
    fs.writeFileSync(path.join(__dirname, 'pure_params.json'), JSON.stringify(params));

    // 调 Python 3.12
    const pyOut = execFileSync('py', ['-3.12', path.join(__dirname, 'h5st_pure.py'), path.join(__dirname, 'pure_params.json')], { encoding: 'utf8' }).trim();
    const pp = pyOut.split(';');

    console.log('===== Python 纯算法 vs SDK 逐段对比 =====');
    let allMatch = true;
    ref.forEach((s, i) => {
        const match = s === pp[i];
        if (!match) allMatch = false;
        console.log(`seg${i + 1}: len ${s.length}/${pp[i] ? pp[i].length : 0} ${match ? '✓' : '✗'}`);
        if (!match && pp[i]) {
            let k = 0;
            while (k < s.length && k < pp[i].length && s[k] === pp[i][k]) k++;
            console.log(`  差异@${k}: SDK=${JSON.stringify(s.substring(k, k + 30))} PY=${JSON.stringify(pp[i].substring(k, k + 30))}`);
        }
    });
    console.log(allMatch ? '\n🎉 Python 版与 SDK 全部 10 段逐字节一致！' : '\n✗ 存在差异');
})();
