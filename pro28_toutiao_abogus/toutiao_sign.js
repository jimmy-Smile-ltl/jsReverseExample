/**
 * 今日头条 a_bogus / msToken 签名模块 v8
 *
 * 补环境: toutiao_env_full.js + dom_prototypes.js
 * a_bogus: 168/172 位 (取决于环境完整度，两种长度均有效)
 * HTTP: 需 curl_cffi 绕过 TLS 指纹 (impersonate="chrome146")
 *
 * 用法:
 *   node extract/toutiao_sign.js "channel_id=0&..."
 *   或 require('./toutiao_sign.js').getSignature("channel_id=0&...")
 */

const path = require('path');
const EXT = __dirname;

let _initialized = false;

function init() {
    if (_initialized) return;

    // 1. 完整浏览器环境
    require('./toutiao_env_full.js');

    // 2. 加载 SDK
    [   'bdms_browser.js',
        'sdk-glue.js',
        'runtime_bundler_52.js'
    ].forEach(f => {
        try {
            require(path.join(EXT, f));
        } catch (e) {
            console.error('[load] FAIL:', f, '-', e.message);
            throw e;
        }
    });

    // 3. 初始化 SDK
    window._SdkGlueInit({
        self: { aid: 24, pageId: 6457 },
        bdms: { aid: 24, pageId: 6457, paths: ['/api/pc/list/feed'] }
    });

    _initialized = true;
}

/**
 * 计算 a_bogus + msToken
 * @param {string} queryString - URL 参数字符串
 * @returns {Promise<{a_bogus: string, msToken: string}>}
 */
async function getSignature(queryString) {
    init();

    const base = 'https://www.toutiao.com/api/pc/list/feed';
    const url = queryString.startsWith('http') ? queryString
              : queryString.startsWith('?') ? base + queryString
              : base + '?' + queryString;

    // Hook URLSearchParams 捕获签名
    let a_bogus = '', msToken = '';
    const OrigAppend = URLSearchParams.prototype.append;
    URLSearchParams.prototype.append = function(name, value) {
        if (name === 'a_bogus') a_bogus = String(value);
        if (name === 'msToken') msToken = String(value);
        return OrigAppend.apply(this, arguments);
    };

    // 触发拦截器链签名
    try { const r = await window.fetch(url); await r.text().catch(() => {}); } catch (_) {}
    await new Promise(r => setTimeout(r, 600));

    return { a_bogus, msToken };
}

// CLI
if (require.main === module) {
    const query = process.argv[2];
    if (!query) {
        console.error('Usage: node toutiao_sign.js "<query_string>"');
        process.exit(1);
    }
    getSignature(query).then(r => {
        console.log(JSON.stringify(r));
        setTimeout(() => process.exit(0), 500);
    }).catch(e => { console.error('Error:', e.message); process.exit(1); });
}

module.exports = { getSignature, init };
