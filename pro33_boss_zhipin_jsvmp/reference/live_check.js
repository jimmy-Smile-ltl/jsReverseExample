// 线上验证（2026-08-29 实测 5/5）：抓 302 挑战 → 生成 token → Cookie 重放
// 依赖 main.py 的 generate_token；PYTHON 环境变量可指定解释器（默认 py）
const https = require('https');
const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const PY = process.env.PYTHON || 'py';   // Python 3 命令（Windows 可用 py）
const HERE = __dirname;
const PROJ = path.join(HERE, '..');

function get(url, headers) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, { headers: headers || {}, rejectUnauthorized: false }, res => {
      const buf = [];
      res.on('data', d => buf.push(d));
      res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, body: Buffer.concat(buf) }));
    });
    req.on('error', reject);
    req.setTimeout(15000, () => { req.destroy(new Error('timeout')); });
  });
}

async function fetchPage(url) {
  const r1 = await get(url);
  if (r1.status === 200) return { ok: true, body: r1.body, note: 'direct' };
  const loc = r1.headers.location;
  if (!loc || r1.status !== 302) return { ok: false, note: 'status ' + r1.status };
  const u = new URL(loc, 'https://m.zhipin.com');
  const seed = decodeURIComponent(u.searchParams.get('seed') || '');
  const ts = Number(u.searchParams.get('ts'));
  const name = u.searchParams.get('name');
  const tmpPy = path.join(HERE, '_gen_tmp.py');
  fs.writeFileSync(tmpPy, [
    'import sys',
    "sys.path.insert(0, r'" + HERE.replace(/\\/g, '\\\\') + "')",
    'from main import generate_token',
    `print(generate_token(${JSON.stringify(seed)}, ${ts}))`,
  ].join('\n'));
  const token = execSync(`"${PY}" "${tmpPy}"`).toString().trim();
  fs.unlinkSync(tmpPy);
  const url2 = url + '&_security_check=1_' + Date.now();
  const r2 = await get(url2, { Cookie: '__zp_stoken__=' + encodeURIComponent(token) });
  if (r2.status === 200) {
    return { ok: true, body: r2.body, note: 'challenge->200, seed=' + seed.slice(0, 8) + ', name=' + name };
  }
  return { ok: false, note: '2nd status ' + r2.status + ' loc ' + (r2.headers.location || '').slice(0, 60) };
}

(async () => {
  const url = 'https://m.zhipin.com/c101270100-p100102/?ka=search_100102';
  for (let i = 1; i <= 5; i++) {
    const r = await fetchPage(url);
    console.log(`[${i}]`, r.ok ? '✅ 200' : '❌ ' + r.note, r.ok ? r.body.length + ' bytes' : '');
  }
})().catch(e => console.error('ERR', e.message));
