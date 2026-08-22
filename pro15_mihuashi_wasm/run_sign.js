/**
 * 米画师 M-S 签名 Node.js WASM 运行器 (生产版本)
 *
 * 用法:
 *   const { createSigner } = require('./run_sign.js');
 *   const signer = await createSigner();
 *   const m_s = signer.sign('/api/v1/artworks/search?page=1&type=recent', Math.floor(Date.now()/1000));
 *   signer.free();
 *
 * 补环境要点:
 *   1. instanceof_Window → 强制返回 true (Node.js 无 Window)
 *   2. document.querySelector → 返回带 getAttribute 的伪元素
 *   3. navigator → 提供浏览器指纹属性
 *   4. crypto → 桥接 Node.js crypto 到 Web Crypto API
 */

const fs = require('fs');
const path = require('path');
const nodeCrypto = require('crypto');

// ============== 浏览器 API 补丁 ==============

// 1. Web Crypto API
function ensureCrypto() {
    const gc = globalThis.crypto || {};
    if (!gc.getRandomValues) {
        gc.getRandomValues = function(buf) {
            const bytes = nodeCrypto.randomBytes(buf.length);
            buf.set(new Uint8Array(bytes.buffer, bytes.byteOffset, buf.length));
            return buf;
        };
    }
    if (!gc.randomUUID) gc.randomUUID = () => nodeCrypto.randomUUID();
    if (!gc.subtle) {
        gc.subtle = {
            digest: async (algo, buf) => {
                const h = nodeCrypto.createHash(algo.toLowerCase().replace('-', ''));
                h.update(new Uint8Array(buf));
                return h.digest().buffer;
            },
        };
    }
    globalThis.crypto = gc;
}

// 2. DOM 元素 — 必须同时支持 getAttribute 和 Reflect.get (属性访问)
function makeElement(tag) {
    const ut = (tag || 'div').toUpperCase();
    return {
        tagName: ut,
        // 直接属性 (Reflect.get 访问)
        get content() { return ut === 'META' ? '米画师,mihuashi,约稿平台,约稿,插画外包,插画外包网站,美术外包平台,游戏美术外包,画师,绘师,美术外包,原画外包,插画师,原画师,原画外包网站' : ''; },
        get href() { return ut === 'LINK' ? 'https://js-assets.mihuashi.com/mhs-assets/legacy/favicon.ico' : ''; },
        get rel() { return ut === 'LINK' ? 'icon' : ''; },
        get name() { return ut === 'META' ? 'keywords' : ''; },
        // getAttribute (WASM import 函数调用)
        getAttribute: function(attrName) {
            if (attrName === 'href') return this.href;
            if (attrName === 'rel') return this.rel;
            if (attrName === 'content') return this.content;
            if (attrName === 'name') return this.name;
            return null;
        },
        setAttribute: function() {},
        style: {},
    };
}

// 3. Document
function ensureDocument() {
    globalThis.document = {
        querySelector: function(sel) {
            if (sel.includes('icon')) return makeElement('LINK');
            if (sel.includes('meta')) return makeElement('META');
            return makeElement('div');
        },
        createElement: makeElement,
        body: { appendChild() {}, querySelector() { return makeElement('div'); } },
        head: { appendChild() {}, querySelector() { return makeElement('div'); } },
    };
}

// 4. Navigator — EXACT values from the page's real browser
function ensureNavigator() {
    globalThis.navigator = {
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
        platform: 'Win32',
        language: 'zh-CN',
        languages: ['zh-CN'],
        hardwareConcurrency: 8,
        deviceMemory: 8,
        vendor: 'Google Inc.',
        vendorSub: '',
        productSub: '20030107',
        cookieEnabled: true,
        appName: 'Netscape',
        appVersion: '5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
        maxTouchPoints: 0,
        webdriver: false,
        onLine: true,
        plugins: { length: 5, item() { return null; }, namedItem() { return null; }, refresh() {} },
        mimeTypes: { length: 5, item() { return null; }, namedItem() { return null; } },
    };
}

// ============== wasm-bindgen 内存管理 ==============

let wasmMemory = null;
let wasmExports = null;

const heap = new Array(128);
for (let i = 0; i < 128; i++) heap[i] = undefined;
heap.push(undefined, null, true, false);
let heapNext = heap.length;

function addHeapObj(obj) { if (heapNext >= heap.length) heap.push(heap.length + 1); const idx = heapNext; heapNext = heap[idx]; heap[idx] = obj; return idx; }
function getObject(idx) { return heap[idx]; }
function dropObject(idx) { if (idx < 132) return; heap[idx] = heapNext; heapNext = idx; }

let cachedMem = null;
function getMem() { if (!cachedMem || cachedMem.buffer !== wasmMemory.buffer) cachedMem = new Uint8Array(wasmMemory.buffer); return cachedMem; }

const td = new TextDecoder('utf-8', { ignoreBOM: true, fatal: true });
function getStr(ptr, len) { return td.decode(getMem().subarray(ptr >>> 0, (ptr + len) >>> 0)); }
function isNull(t) { return t == null; }

let vecLen = 0;
const te = new TextEncoder();
function passStr(arg, malloc, realloc) {
    if (realloc === undefined) {
        const buf = te.encode(arg); const ptr = malloc(buf.length, 1) >>> 0;
        getMem().set(buf, ptr); vecLen = buf.length; return ptr;
    }
    let len = arg.length, ptr = malloc(len, 1) >>> 0; const mem = getMem(); let offset = 0;
    for (; offset < len; offset++) { const code = arg.charCodeAt(offset); if (code > 0x7F) break; mem[ptr + offset] = code; }
    if (offset !== len) {
        if (offset !== 0) arg = arg.slice(offset);
        ptr = realloc(ptr, len, len = offset + arg.length * 3, 1) >>> 0;
        const r = te.encodeInto(arg, getMem().subarray(ptr + offset, ptr + len));
        offset += r.written; ptr = realloc(ptr, len, offset, 1) >>> 0;
    }
    vecLen = offset; return ptr;
}

let dvCache = null; let dvBuf = null;
function getView() { if (!dvCache || dvBuf !== wasmMemory.buffer) { dvBuf = wasmMemory.buffer; dvCache = new DataView(wasmMemory.buffer); } return dvCache; }

function handleErr(f) { try { return f(); } catch (e) { wasmExports.__wbindgen_export_0(addHeapObj(e)); } }

// ============== wbg imports ==============
const wbg = {
    __wbindgen_memory: () => addHeapObj(wasmMemory),
    __wbindgen_string_new: (ptr, len) => addHeapObj(getStr(ptr, len)),
    __wbindgen_string_get: function(retPtr, idx) {
        const obj = getObject(idx); const str = typeof obj === 'string' ? obj : undefined;
        const ptr = str === undefined ? 0 : passStr(str, wasmExports.__wbindgen_export_1, wasmExports.__wbindgen_export_2);
        getView().setInt32(retPtr + 4, vecLen, true); getView().setInt32(retPtr + 0, ptr, true);
    },
    __wbindgen_debug_string: function(retPtr, idx) {
        const str = String(getObject(idx)); const ptr = passStr(str, wasmExports.__wbindgen_export_1, wasmExports.__wbindgen_export_2);
        getView().setInt32(retPtr + 4, vecLen, true); getView().setInt32(retPtr + 0, ptr, true);
    },
    __wbindgen_throw: (ptr, len) => { throw new Error(getStr(ptr, len)); },
    __wbindgen_object_clone_ref: (idx) => addHeapObj(getObject(idx)),
    __wbindgen_object_drop_ref: (idx) => { dropObject(idx); },
    __wbindgen_is_object: (idx) => { const o = getObject(idx); return typeof o === 'object' && o !== null ? 1 : 0; },
    __wbindgen_is_function: (idx) => typeof getObject(idx) === 'function' ? 1 : 0,
    __wbindgen_is_string: (idx) => typeof getObject(idx) === 'string' ? 1 : 0,
    __wbindgen_is_undefined: (idx) => getObject(idx) === void 0 ? 1 : 0,
    __wbindgen_number_new: (num) => addHeapObj(num),
    __wbindgen_boolean_get: (idx) => { const v = getObject(idx); return typeof v === 'boolean' ? (v ? 1 : 0) : 2; },
    __wbg_buffer_609cc3eee51ed158: (idx) => addHeapObj(getObject(idx).buffer),
    __wbg_new_a12002a7f91c75be: (idx) => addHeapObj(new Uint8Array(getObject(idx))),
    __wbg_newwithlength_a381634e90c276d4: (len) => addHeapObj(new Uint8Array(len >>> 0)),
    __wbg_newwithbyteoffsetandlength_d97e637ebe145a9a: (bufIdx, offset, len) => addHeapObj(new Uint8Array(getObject(bufIdx), offset >>> 0, len >>> 0)),
    __wbg_set_65595bdd868b3009: (arrIdx, valIdx, offset) => { getObject(arrIdx).set(getObject(valIdx), offset >>> 0); },
    __wbg_subarray_aa9065fa9dc5df96: (arrIdx, start, end) => addHeapObj(getObject(arrIdx).subarray(start >>> 0, end >>> 0)),
    __wbg_call_672a4d21634d4a24: function() { return handleErr(() => addHeapObj(getObject(arguments[0]).call(getObject(arguments[1])))); },
    __wbg_call_7cccdd69e0791ae2: function() { return handleErr(() => addHeapObj(getObject(arguments[0]).call(getObject(arguments[1]), getObject(arguments[2])))); },
    __wbg_newnoargs_105ed471475aaf50: (ptr, len) => addHeapObj(new Function(getStr(ptr, len))),
    __wbg_get_67b2ba62fc30de12: function() { return handleErr(() => { const obj = getObject(arguments[0]); const prop = getObject(arguments[1]); return addHeapObj(Reflect.get(obj, prop)); }); },
    __wbg_set_bb8cecf6a62b9f46: function() { return handleErr(() => Reflect.set(getObject(arguments[0]), getObject(arguments[1]), getObject(arguments[2]))); },
    // 全局对象访问器 — 返回干净的浏览器全局代理 (屏蔽 process/Buffer 等)
    __wbg_static_accessor_GLOBAL_88a902d13a557d07: () => isNull(globalThis.__browserGlobal) ? 0 : addHeapObj(globalThis.__browserGlobal),
    __wbg_static_accessor_GLOBAL_THIS_56578be7e9f832b0: () => isNull(globalThis.__browserGlobal) ? 0 : addHeapObj(globalThis.__browserGlobal),
    __wbg_static_accessor_SELF_37c5d418e4bf5819: () => isNull(globalThis.__browserGlobal) ? 0 : addHeapObj(globalThis.__browserGlobal),
    __wbg_static_accessor_WINDOW_5de37043a91a9c40: () => isNull(globalThis.__browserGlobal) ? 0 : addHeapObj(globalThis.__browserGlobal),
    __wbg_static_accessor_PROCESS_2c90d3b3264f2c90: () => 0,
    __wbg_node_02999533c4ea02e3: (idx) => 0,
    __wbg_process_5c1d670bc53614b8: (idx) => 0,
    __wbg_versions_c71aa1626a93e0a1: (idx) => 0,
    __wbg_require_79b1e9274cde3c87: function() { return 0; },
    __wbg_crypto_ed58b8e10a292839: (idx) => addHeapObj(getObject(idx).crypto),
    __wbg_msCrypto_0a36e2ec3a343d26: (idx) => addHeapObj(getObject(idx).msCrypto),
    __wbg_getRandomValues_bcb4912f16000dc4: function() { return handleErr(() => { getObject(arguments[0]).getRandomValues(getObject(arguments[1])); }); },
    __wbg_randomFillSync_ab2cfe79ebbf2740: function() { return handleErr(() => { getObject(arguments[0]).randomFillSync(getObject(arguments[1])); }); },
    __wbg_navigator_1577371c070c8947: (idx) => { const obj = getObject(idx); const nav = obj ? obj.navigator : undefined; return isNull(nav) ? 0 : addHeapObj(nav); },
    __wbg_document_d249400bd7bd996d: (idx) => { const obj = getObject(idx); const doc = obj ? obj.document : undefined; return isNull(doc) ? 0 : addHeapObj(doc); },
    __wbg_querySelector_c69f8b573958906b: function() { return handleErr(() => { const el = getObject(arguments[0]); const sel = getStr(arguments[1], arguments[2]); const found = el.querySelector(sel); return isNull(found) ? 0 : addHeapObj(found); }); },
    __wbg_getAttribute_ea5166be2deba45e: function(retPtr, elIdx, namePtr, nameLen) {
        const el = getObject(elIdx); const attrName = getStr(namePtr, nameLen);
        const val = el && el.getAttribute ? el.getAttribute(attrName) : null;
        const ptr = isNull(val) ? 0 : passStr(val, wasmExports.__wbindgen_export_1, wasmExports.__wbindgen_export_2);
        getView().setInt32(retPtr + 4, vecLen, true); getView().setInt32(retPtr + 0, ptr, true);
    },
    __wbg_instanceof_Window_def73ea0955fc569: function(idx) {
        // 强制返回 true - Node.js 没有 Window 构造函数
        return 1;
    },
};

// ============== Signtool 封装 ==============

class Signtool {
    constructor() {
        this.ptr = wasmExports.signtool_new() >>> 0;
        if (!this.ptr) throw new Error('signtool_new returned null');
    }

    /**
     * 生成 M-S 签名
     * @param {string} url - encodeURI 编码后的 URL 路径
     * @param {number} ts - Unix 时间戳(秒)
     * @returns {string} M-S 签名
     */
    sign(url, ts) {
        let rp, rl;
        try {
            const sp = wasmExports.__wbindgen_add_to_stack_pointer(-16);
            const up = passStr(url, wasmExports.__wbindgen_export_1, wasmExports.__wbindgen_export_2);
            const ul = vecLen;
            wasmExports.signtool_sign(sp, this.ptr, up, ul, ts);
            const v = getView();
            const ptr = v.getInt32(sp + 0, true);
            const len = v.getInt32(sp + 4, true);
            const errFlag = v.getInt32(sp + 12, true);
            if (errFlag) { dropObject(v.getInt32(sp + 8, true)); throw new Error('signtool_sign error'); }
            rp = ptr; rl = len;
            return getStr(ptr, len);
        } finally {
            wasmExports.__wbindgen_add_to_stack_pointer(16);
            if (rp || rl) wasmExports.__wbindgen_export_3(rp, rl, 1);
        }
    }

    free() {
        if (this.ptr) { wasmExports.__wbg_signtool_free(this.ptr, 0); this.ptr = 0; }
    }
}

// ============== 初始化入口 ==============

let _initPromise = null;

async function createSigner(wasmPath) {
    if (!wasmPath) {
        wasmPath = process.env.MHS_WASM_PATH || path.join(__dirname, 'mhs_fe_sign_bg.wasm');
    }

    // 环境补丁
    ensureCrypto();
    ensureDocument();
    ensureNavigator();

    // 关键: 创建干净的浏览器全局对象 (纯对象，不含 Node.js process/Buffer 等)
    // WASM 通过 Reflect.get 访问全局对象属性时会检测到 Node.js 特征
    const browserGlobal = {
        crypto: globalThis.crypto,
        document: globalThis.document,
        navigator: globalThis.navigator,
        self: null,    // 将在下面设置
        window: null,  // 将在下面设置
        location: { href: 'https://www.mihuashi.com/artworks', protocol: 'https:', hostname: 'www.mihuashi.com' },
        msCrypto: undefined,
        // 不包含: process, Buffer, require, __dirname, __filename, module, exports, global
    };
    browserGlobal.self = browserGlobal;
    browserGlobal.window = browserGlobal;
    globalThis.__browserGlobal = browserGlobal;

    // 设置 Window 构造函数
    if (typeof globalThis.Window === 'undefined') {
        globalThis.Window = Object;
    }

    // 加载 WASM
    const wasmBytes = fs.readFileSync(wasmPath);

    // signtool_new 可能因随机数种子而间歇性失败
    // 失败后会污染 WASM 内部状态，需要重新实例化
    const maxAttempts = 30;
    let lastError = null;

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
        // 重置 heap（WASM 实例化期间的状态）
        for (let i = 0; i < 128; i++) heap[i] = undefined;
        heap.length = 132;
        heap[128] = undefined; heap[129] = null; heap[130] = true; heap[131] = false;
        heapNext = 132;

        const result = await WebAssembly.instantiate(wasmBytes, { wbg });
        wasmExports = result.instance.exports;
        wasmMemory = wasmExports.memory;

        // 重置内存缓存
        cachedMem = null;
        dvCache = null; dvBuf = null;

        try {
            return new Signtool();
        } catch (e) {
            lastError = e;
        }
    }

    throw new Error(`Signtool creation failed after ${maxAttempts} attempts: ${lastError?.message}`);
}

// ============== 直接运行测试 ==============

if (require.main === module) {
    (async () => {
        console.log('米画师 M-S 签名 Node.js 运行器');
        console.log('初始化...');
        const signer = await createSigner();
        console.log('初始化完成!\n');

        const testUrl = '/api/v1/artworks/search?page=1&type=recent';
        const ts = Math.floor(Date.now() / 1000);
        console.log(`签名测试:`);
        console.log(`  URL: ${testUrl}`);
        console.log(`  TS:  ${ts}`);

        const sig = signer.sign(encodeURI(testUrl), ts);
        console.log(`  M-S: ${sig}`);
        console.log(`  长度: ${sig.length}`);

        // 验证非确定性
        const sig2 = signer.sign(encodeURI(testUrl), ts);
        console.log(`  非确定性: ${sig !== sig2} (相同输入产生不同输出)`);

        signer.free();
        console.log('\n✅ 成功!');
    })().catch(err => { console.error('失败:', err.message); process.exit(1); });
} else {
    module.exports = { createSigner, Signtool };
}
