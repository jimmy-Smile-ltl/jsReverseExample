/**
 * 参考脚本：京东主站 h5st v5.3 Node 纯算路线（2026-08-30 实测 code=0）
 * 注意：本文件依赖同目录的 sign.js / local_cache.json（JD SDK 与登录态），
 *       仓库未随附；仅保留路线代码作学习参考，不能直接运行。
 */
/**
 * sign_v53_pure.js — 京东主站 h5st v5.3 纯算方案（无浏览器、无 RPC）
 *
 * 流程:
 *   1. cactus.jd.com/request_algo (version=5.3 + localTk) → {tk, fp, algo}（token 自动刷新）
 *   2. 写入 localStorage 种子（WQ_dy1_vk / WQ_dy1_tk_algo / WQ_dy1_pFlag）
 *   3. 复用 sign.js 的补环境生成 1103 chars h5st
 *
 * 依赖: sign.js（同目录）、curl_cffi（请求层，Python 侧）
 * 用法: node sign_v53_pure.js [--refresh] [--save cache.json]
 *
 * token/algo 缓存到 local_cache.json（token 有效期 1 天，cactus 用 localTk 刷新）
 */
const https = require('https');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const APP_ID = 'b5216';
const APPID = 'www-jd-com';
const PAGE_URL = 'https://www.jd.com/';
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36';
const CACHE_FILE = path.join(__dirname, 'local_cache.json');

// 浏览器真实指纹（与 fp 配套，env patch 用）
const CV1 = '0a52a8929510e9fb19f80acb099176a0';
const WGL1 = '198cd014ef66a0660ae5d2076dc0f1b9';

function post(url, data, headers) {
    return new Promise((resolve, reject) => {
        const body = JSON.stringify(data);
        const u = new URL(url);
        const req = https.request({
            hostname: u.hostname, path: u.pathname + u.search, method: 'POST',
            headers: Object.assign({ 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) }, headers),
        }, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => resolve({ status: res.statusCode, body: d }));
        });
        req.on('error', reject);
        req.write(body);
        req.end();
    });
}

function buildEnv(fp, localTk) {
    return {
        ai: APP_ID, fp, wk: 0,
        extend: { wd: 0, l: 0, ls: 5, wk: 0, bu1: '0.1.4', bu3: 41, bu4: 0, bu5: 0, bu6: 28, bu7: 0, bu8: 0, random: Math.random().toString(36).substring(2, 13), bu12: -8, bu10: 14, bu11: 4, bu13: 'Fc' },
        sua: 'Windows NT 10.0; Win64; x64', pp: {}, pf: 'Win32', v: 'h5_file_v5.3.4',
        random: Math.random().toString(36).substring(2, 13),
        url: PAGE_URL, og: 'https://www.jd.com', pr: 1, re: '', referer: PAGE_URL,
        canvas: CV1, webglFp: WGL1, ccn: 16, bu4: '0', bu14: 'jmqmEtVELq',
        t: Date.now(),
    };
}

async function refreshToken(oldCache) {
    const fp = oldCache && oldCache.fp || Math.random().toString(36).substring(2, 18);
    const localTk = oldCache && oldCache.tk || '';
    const env = buildEnv(fp, localTk);
    const expandParams = Buffer.from(JSON.stringify(env, null, 2), 'utf8').toString('base64');
    const data = {
        version: '5.3', fp, appId: APP_ID, timestamp: Date.now(),
        platform: 'web', expandParams, fv: 'h5_file_v5.3.4', localTk,
    };
    const r = await post('https://cactus.jd.com/request_algo?g_ty=ajax', data, {
        'Accept': 'application/json', 'Origin': 'https://www.jd.com', 'Referer': PAGE_URL, 'User-Agent': UA,
    });
    const j = JSON.parse(r.body);
    if (j.status !== 200 || !j.data || !j.data.result) throw new Error('cactus fail: ' + r.body.substring(0, 200));
    const res = j.data.result;
    // algo 的 tk/algo 打包成 WQ_dy1_tk_algo 的 v 格式: CryptoJS b64(Utf8) 编码的 JSON {tk, algo}
    const inner = JSON.stringify({ tk: res.tk, algo: res.algo });
    const b64 = Buffer.from(inner, 'utf8').toString('base64');
    const cache = { fp: res.fp, tk: res.tk, algo: res.algo, tk_v: b64, ts: Date.now() };
    fs.writeFileSync(CACHE_FILE, JSON.stringify(cache, null, 2));
    console.log('[cactus] refreshed: fp=' + res.fp + ' tk=' + res.tk.substring(0, 20) + '...');
    return cache;
}

function loadCache() {
    try {
        const c = JSON.parse(fs.readFileSync(CACHE_FILE, 'utf8'));
        // token 有效期 1 天
        if (c && c.ts && Date.now() - c.ts < 86400000 && c.tk_v) return c;
    } catch (e) { }
    return null;
}

async function main() {
    const args = process.argv.slice(2);
    let cache = args.includes('--refresh') ? null : loadCache();
    if (!cache) cache = await refreshToken(loadCache());

    // 更新 sign.js 的种子（FP / TK_V / CV1 / WGL1）
    let signSrc = fs.readFileSync(path.join(__dirname, 'sign.js'), 'utf8');
    signSrc = signSrc.replace(/var FP = '[^']*';/, `var FP = '${cache.fp}';`);
    signSrc = signSrc.replace(/var TK_V = '[^']*';/, `var TK_V = '${cache.tk_v}';`);
    signSrc = signSrc.replace(/var CV1 = '[^']*';/, `var CV1 = '${CV1}';`);
    signSrc = signSrc.replace(/var WGL1 = '[^']*';/, `var WGL1 = '${WGL1}';`);
    fs.writeFileSync(path.join(__dirname, 'sign.js'), signSrc);

    // 调 sign.js 生成（JD_PATCH_ENV=1）
    const { execSync } = require('child_process');
    execSync('node sign.js', { cwd: __dirname, env: Object.assign({}, process.env, { JD_PATCH_ENV: '1' }), stdio: 'inherit' });
    const h5st = fs.readFileSync(path.join(__dirname, 'node_h5st.txt'), 'utf8').trim();
    console.log('[h5st]', h5st.length, 'chars');
    console.log(h5st);
}

main().catch(e => { console.error('ERROR:', e.message); process.exit(1); });
