/**
 * toutiao_env_full.js — 完整浏览器环境（集成所有已确认有效的修复）
 *
 * 已确认有效的改进:
 *   v5: window.chrome + outerWidth/Height → 144→160 (+16)
 *   fp: 原型链修复 (instanceof Navigator/Document/Window/Screen)
 *   plus: 全部 navigator 属性 + 完整 localStorage + 完整 document
 */

// ===== Native toString =====
const _nts = Symbol('native_toString');
(function() {
    const orig = Function.prototype.toString;
    Object.defineProperty(Function.prototype, 'toString', {
        value: function toString() { return this[_nts] || orig.call(this); },
        configurable: true, writable: true
    });
})();
function markNative(fn, name) {
    Object.defineProperty(fn, _nts, {
        value: `function ${name || fn.name || ''}() { [native code] }`,
        configurable: true
    });
    return fn;
}
// __nts_symbol and __markNative will be exported after G is defined
function setTag(obj, tag) {
    Object.defineProperty(obj, Symbol.toStringTag, { value: tag, configurable: true });
}
function noop() {}
function safeDef(obj, key, desc) {
    const base = { enumerable: true, configurable: true };
    if (desc.get || desc.set) Object.defineProperty(obj, key, Object.assign(base, desc));
    else Object.defineProperty(obj, key, Object.assign(base, { writable: true }, desc));
}

const G = globalThis;

// Export native toString helpers
G.__nts_symbol = _nts;
G.__markNative = markNative;

// ===== Window =====
G.Window = function Window() {}; setTag(G.Window.prototype, 'Window'); markNative(G.Window, 'Window');
G.window = G; Object.setPrototypeOf(G, G.Window.prototype);
G.self = G; G.top = G; G.parent = G;
try { delete G.GLOBAL; } catch(e) {} try { delete G.root; } catch(e) {}

// ===== Navigator =====
G.Navigator = function Navigator() {}; setTag(G.Navigator.prototype, 'Navigator'); markNative(G.Navigator, 'Navigator');
const ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36';
const NP = G.Navigator.prototype;
safeDef(NP, 'userAgent', { get: () => ua });
safeDef(NP, 'appVersion', { get: () => '5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36' });
safeDef(NP, 'platform', { get: () => 'Win32' });
safeDef(NP, 'language', { get: () => 'zh-CN' });
safeDef(NP, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
safeDef(NP, 'vendor', { get: () => 'Google Inc.' });
safeDef(NP, 'appName', { get: () => 'Netscape' });
safeDef(NP, 'appCodeName', { get: () => 'Mozilla' });
safeDef(NP, 'product', { get: () => 'Gecko' });
safeDef(NP, 'productSub', { get: () => '20030107' });
safeDef(NP, 'vendorSub', { get: () => '' });
safeDef(NP, 'cookieEnabled', { get: () => true });
safeDef(NP, 'maxTouchPoints', { get: () => 0 });
safeDef(NP, 'hardwareConcurrency', { get: () => 8 });
safeDef(NP, 'webdriver', { get: () => false });
safeDef(NP, 'onLine', { get: () => true });
safeDef(NP, 'doNotTrack', { get: () => null });
safeDef(NP, 'pdfViewerEnabled', { get: () => true });
safeDef(NP, 'deviceMemory', { get: () => 8 });
safeDef(NP, 'userActivation', { get: () => ({ isActive: false, hasBeenActive: false }) });
safeDef(NP, 'globalPrivacyControl', { get: () => false });

// Plugins/MimeTypes
(function() {
    const arr = [0,1,2,3,4].map(i => ({ name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: '', length: 1 }));
    arr.item = function(i) { return this[i]; };
    arr.namedItem = function(n) { return null; };
    arr.refresh = function() {};
    safeDef(NP, 'plugins', { get: () => arr });
    const mime = [{ type: 'application/pdf', suffixes: 'pdf', description: '' }];
    mime.item = function(i) { return this[i]; };
    mime.namedItem = function(n) { return null; };
    safeDef(NP, 'mimeTypes', { get: () => mime });
})();

// Navigator objects
const pNoop = function() { return Promise.resolve({}); };
safeDef(NP, 'sendBeacon', { value: function() { return true; } });
safeDef(NP, 'connection', { get: () => ({ effectiveType: '4g', downlink: 10, rtt: 50, saveData: false, type: 'cellular' }) });
safeDef(NP, 'geolocation', { get: () => ({ getCurrentPosition: noop, watchPosition: noop, clearWatch: noop }) });
safeDef(NP, 'clipboard', { get: () => ({ read: pNoop, write: pNoop, readText: () => Promise.resolve(''), writeText: () => Promise.resolve() }) });
safeDef(NP, 'credentials', { get: () => ({ get: pNoop, store: pNoop, create: pNoop }) });
safeDef(NP, 'permissions', { get: () => ({ query: () => Promise.resolve({ state: 'prompt' }) }) });
safeDef(NP, 'mediaDevices', { get: () => ({ enumerateDevices: () => Promise.resolve([]), getUserMedia: () => Promise.resolve({}) }) });
safeDef(NP, 'serviceWorker', { get: () => ({ register: () => Promise.resolve({}), ready: Promise.resolve({}), controller: null }) });
safeDef(NP, 'storage', { get: () => ({ estimate: () => Promise.resolve({ quota: 107374182400, usage: 0 }) }) });
safeDef(NP, 'keyboard', { get: () => ({ getLayoutMap: () => Promise.resolve(new Map()) }) });
safeDef(NP, 'scheduling', { get: () => ({ isInputPending: () => false }) });
safeDef(NP, 'locks', { get: () => ({ request: pNoop }) });
safeDef(NP, 'gpu', { get: () => ({}) });
safeDef(NP, 'wakeLock', { get: () => ({ request: () => Promise.resolve({ release: () => Promise.resolve() }) }) });
safeDef(NP, 'serial', { get: () => ({}) });
safeDef(NP, 'hid', { get: () => ({}) });
safeDef(NP, 'usb', { get: () => ({}) });
safeDef(NP, 'xr', { get: () => ({}) });
safeDef(NP, 'bluetooth', { get: () => ({}) });
safeDef(NP, 'virtualKeyboard', { get: () => ({}) });
safeDef(NP, 'managed', { get: () => ({}) });
safeDef(NP, 'mediaCapabilities', { get: () => ({}) });
safeDef(NP, 'mediaSession', { get: () => ({ metadata: null, playbackState: 'none' }) });
safeDef(NP, 'presentation', { get: () => ({ defaultRequest: null }) });
safeDef(NP, 'devicePosture', { get: () => ({ type: 'continuous' }) });
safeDef(NP, 'storageBuckets', { get: () => ({}) });
safeDef(NP, 'windowControlsOverlay', { get: () => ({ visible: false }) });
safeDef(NP, 'webkitTemporaryStorage', { get: () => ({}) });
safeDef(NP, 'webkitPersistentStorage', { get: () => ({}) });
safeDef(NP, 'login', { get: () => ({}) });
safeDef(NP, 'ink', { get: () => ({}) });
safeDef(NP, 'adAuctionComponents', { get: () => [] });
safeDef(NP, 'protectedAudience', { get: () => ({}) });
safeDef(NP, 'userAgentData', { get: () => ({ brands: [{brand:'Chromium',version:'146'},{brand:'Google Chrome',version:'146'},{brand:'Not/A)Brand',version:'99'}], mobile: false, platform: 'Windows' }) });

// Navigator instance
const nav = {};
Object.setPrototypeOf(nav, NP);
safeDef(G, 'navigator', { value: nav });

// ===== Location =====
G.Location = function Location() {}; setTag(G.Location.prototype, 'Location'); markNative(G.Location, 'Location');
const loc = {}; Object.setPrototypeOf(loc, G.Location.prototype);
const wid = String(Date.now() - 3000);
['href','origin','protocol','host','hostname','port','pathname','search','hash'].forEach(k => {
    const vals = { href: 'https://www.toutiao.com/?wid='+wid, origin: 'https://www.toutiao.com', protocol: 'https:', host: 'www.toutiao.com', hostname: 'www.toutiao.com', port: '', pathname: '/', search: '?wid='+wid, hash: '' };
    safeDef(G.Location.prototype, k, { get: () => vals[k] });
});
safeDef(loc, 'ancestorOrigins', { value: {} });
safeDef(G, 'location', { value: loc });

// ===== Document =====
G.HTMLDocument = function HTMLDocument() {}; setTag(G.HTMLDocument.prototype, 'HTMLDocument'); markNative(G.HTMLDocument, 'HTMLDocument');
function mkEl(t) { return { tagName: String(t||'div').toUpperCase(), nodeName: '', nodeType: 1, style: {}, classList: { add:noop, remove:noop, contains:()=>false }, setAttribute:noop, getAttribute:()=>null, removeAttribute:noop, appendChild:c=>c, addEventListener:noop, removeEventListener:noop }; }
var doc = {}; Object.setPrototypeOf(doc, G.HTMLDocument.prototype);
doc.cookie = 'gfkadpd=24,6457';
doc.referrer = 'https://www.toutiao.com/';
doc.URL = doc.documentURI = 'https://www.toutiao.com/?wid=' + wid;
doc.domain = 'www.toutiao.com';
doc.hidden = false; doc.visibilityState = 'visible'; doc.readyState = 'complete';
doc.webkitHidden = false; doc.webkitVisibilityState = 'visible';
doc.compatMode = 'CSS1Compat'; doc.contentType = 'text/html'; doc.characterSet = 'UTF-8';
doc.lastModified = '06/12/2026 00:00:00'; doc.designMode = 'off';
doc.documentElement = Object.assign(mkEl('html'), { clientWidth: 1920, clientHeight: 1080 });
doc.head = mkEl('head'); doc.body = mkEl('body');
doc.all = { length: 0 };
doc.scripts = { length: 0 }; doc.styleSheets = { length: 0 }; doc.images = { length: 0 }; doc.forms = { length: 0 }; doc.links = { length: 0 };
doc.createElement = t => mkEl(t);
doc.createEvent = () => ({ initEvent: noop });
doc.createTextNode = t => ({ nodeType: 3, textContent: String(t||'') });
doc.addEventListener = doc.removeEventListener = noop;
doc.getElementsByTagName = () => []; doc.getElementById = () => null;
doc.querySelector = () => null; doc.querySelectorAll = () => [];
doc.hasFocus = () => true;
doc.currentScript = { getAttribute: n => n==='project-id'?'52':null, src: '' };
safeDef(G, 'document', { value: doc });

// ===== Screen =====
G.Screen = function Screen() {}; setTag(G.Screen.prototype, 'Screen'); markNative(G.Screen, 'Screen');
const scr = {}; Object.setPrototypeOf(scr, G.Screen.prototype);
safeDef(G.Screen.prototype, 'width', { get: () => 1920 });
safeDef(G.Screen.prototype, 'height', { get: () => 1080 });
safeDef(G.Screen.prototype, 'availWidth', { get: () => 1920 });
safeDef(G.Screen.prototype, 'availHeight', { get: () => 1032 });
safeDef(G.Screen.prototype, 'colorDepth', { get: () => 24 });
safeDef(G.Screen.prototype, 'pixelDepth', { get: () => 24 });
safeDef(G, 'screen', { value: scr });

// ===== History =====
G.History = function History() {}; setTag(G.History.prototype, 'History'); markNative(G.History, 'History');
const hist = {}; Object.setPrototypeOf(hist, G.History.prototype);
safeDef(G.History.prototype, 'length', { get: () => 5 });
['back','forward','go','pushState','replaceState'].forEach(m => safeDef(hist, m, { value: noop }));
safeDef(G, 'history', { value: hist });

// ===== Performance =====
const timeOrigin = Date.now() - 15000;
G.Performance = function Performance() {}; setTag(G.Performance.prototype, 'Performance'); markNative(G.Performance, 'Performance');
const perf = {}; Object.setPrototypeOf(perf, G.Performance.prototype);
safeDef(perf, 'timeOrigin', { value: timeOrigin });
safeDef(perf, 'now', { value: markNative(() => Date.now() - timeOrigin, 'now') });
safeDef(perf, 'timing', { value: { navigationStart: timeOrigin, domLoading: timeOrigin+500, domComplete: timeOrigin+3000 } });
safeDef(perf, 'getEntriesByType', { value: markNative(() => [], 'getEntriesByType') });
safeDef(perf, 'getEntries', { value: markNative(() => [], 'getEntries') });
safeDef(perf, 'getEntriesByName', { value: markNative(() => [], 'getEntriesByName') });
safeDef(perf, 'mark', { value: markNative(noop, 'mark') });
safeDef(perf, 'measure', { value: markNative(noop, 'measure') });
safeDef(perf, 'clearMarks', { value: markNative(noop, 'clearMarks') });
safeDef(perf, 'clearMeasures', { value: markNative(noop, 'clearMeasures') });
safeDef(perf, 'clearResourceTimings', { value: markNative(noop, 'clearResourceTimings') });
safeDef(perf, 'setResourceTimingBufferSize', { value: markNative(noop, 'setResourceTimingBufferSize') });
safeDef(perf, 'markResourceTiming', { value: markNative(noop, 'markResourceTiming') });
safeDef(G, 'performance', { value: perf });

// ===== Storage =====
function createStorage(init) {
    let store = Object.create(null);
    if (init) for (const k in init) store[k] = String(init[k]);
    const obj = {};
    safeDef(obj, 'length', { get() { return Object.keys(store).length; } });
    safeDef(obj, 'getItem', { value: markNative(k => store[k] || null, 'getItem') });
    safeDef(obj, 'setItem', { value: markNative(function(k,v) { store[String(k)]=String(v); this[String(k)]=String(v); }, 'setItem') });
    safeDef(obj, 'removeItem', { value: markNative(k => { delete store[String(k)]; }, 'removeItem') });
    safeDef(obj, 'clear', { value: markNative(() => { store = Object.create(null); }, 'clear') });
    safeDef(obj, 'key', { value: markNative(i => Object.keys(store)[i]||null, 'key') });
    setTag(obj, 'Storage');
    return obj;
}
G.localStorage = createStorage({
    'xmst': 'Xvol04ct86MbmAaStLtD_ea-PGjxK-7xF1Pgk5ucfWWVzRdml63rHsJYldf6TkqCNTHdWDtUs6TUGFteQ_TV4YLVdiMH2dDAUVV7m_a5BOX-zUi35tgqZQ==',
    '__tea_cache_first_24': '1',
    'tt_scid': 'QoyirT6OKNlRNbQkg57KDulJTo0.XVd3sp4EHhcUT5rqO858lL-L.NrWC35PFeNk1b0e',
    '__tea_cache_tokens_24': '{"web_id":"7647552033054410286","timestamp":1780584502354,"_type_":"default"}',
    '_byted_param_sw': '',
    'web_runtime_security_uid': '729f6b00-d027-4f97-ac68-bf5042d4c2db',
    '__tea_cache_refer_24': '',
    '__is_visited_home': '1',
    'ttcid': '676afac132b84da3b109a65a6a459d8d16',
});
G.sessionStorage = createStorage({});

// ===== 关键补丁 =====
G.chrome = { app: { isInstalled: false }, runtime: {}, loadTimes: noop, csi: noop };
G.outerWidth = G.innerWidth = 1920;
G.outerHeight = G.innerHeight = 947;
G.devicePixelRatio = 1;
G.name = ''; G.closed = false; G.length = 0; G.frameElement = null;
G.scrollX = G.pageXOffset = 0; G.scrollY = G.pageYOffset = 0;
G.screenX = G.screenLeft = 0; G.screenY = G.screenTop = 0;
G.toolbar = G.menubar = G.scrollbars = G.statusbar = G.personalbar = G.locationbar = { visible: true };
G.matchMedia = () => ({ matches:false, media:'', addListener:noop, removeListener:noop, addEventListener:noop, removeEventListener:noop });
G.getComputedStyle = () => ({ getPropertyValue: () => '' });
G.getSelection = () => null;
G.external = {}; G.sidebar = {};
G.visualViewport = { width: 1920, height: 947, scale: 1, offsetLeft: 0, offsetTop: 0 };

G.atob = markNative(s => Buffer.from(String(s), 'base64').toString('binary'), 'atob');
G.btoa = markNative(s => Buffer.from(String(s), 'binary').toString('base64'), 'btoa');

// ===== 关键签名时访问的属性 (168/172) =====
// body 尺寸必须精确匹配浏览器
var body = G.document.body;
body.clientWidth = 1920; body.clientHeight = 2387;
body.offsetWidth = 1920; body.offsetHeight = 2387;
body.scrollWidth = 1920; body.scrollHeight = 2387;
body.clientTop = 0; body.clientLeft = 0;
G.document.documentElement.clientHeight = 2387;
G.document.execCommand = function() { return false; };

// DOMTokenList — 正确构造函数 (VM 检查 classList.constructor)
G.DOMTokenList = function DOMTokenList() {};
G.DOMTokenList.prototype = Object.create(Object.prototype);
G.DOMTokenList.prototype.constructor = G.DOMTokenList;
G.__markNative(G.DOMTokenList, 'DOMTokenList');
G.DOMTokenList.prototype.add = function(t) {};
G.DOMTokenList.prototype.remove = function(t) {};
G.DOMTokenList.prototype.contains = function(t) { return false; };
G.DOMTokenList.prototype.toggle = function(t) { return false; };
G.DOMTokenList.prototype.item = function(i) { return null; };
G.DOMTokenList.prototype.toString = function() { return ''; };
Object.defineProperty(G.DOMTokenList.prototype, 'length', { get: function() { return 0; }, configurable: true });
Object.defineProperty(G.DOMTokenList.prototype, 'value', { get: function() { return ''; }, set: function(v) {}, configurable: true });
Object.defineProperty(G.DOMTokenList.prototype, Symbol.toStringTag, { value: 'DOMTokenList', configurable: true });

// HTMLAnchorElement (VM 在浏览器中创建 a 元素)
G.HTMLAnchorElement = function HTMLAnchorElement() {};

// createElement 增强: canvas toDataURL, 所有元素 classList=DOMTokenList
var _origCE = G.document.createElement;
G.document.createElement = function(tag) {
    var t = String(tag||'div').toLowerCase();
    var el = _origCE(tag);
    el.clientWidth = 0; el.clientHeight = 0;
    el.offsetWidth = 0; el.offsetHeight = 0;
    el.innerHTML = ''; el.textContent = '';
    el.tagName = t.toUpperCase();
    el.href = ''; el.rel = ''; el.target = '';
    el.protocol = ':'; el.host = ''; el.hostname = ''; el.port = '';
    el.pathname = ''; el.search = ''; el.hash = ''; el.origin = '://';
    el.classList = Object.create(G.DOMTokenList.prototype);
    if (t === 'canvas') {
        el.width = 300; el.height = 150;
        el.toDataURL = function() { return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAARgAAAA8CAYAAABmgISf'; };
    }
    return el;
};
// ===== 关键签名时访问的属性 END =====

let rafId = 0;
G.requestAnimationFrame = markNative(cb => { setTimeout(() => cb(Date.now()), 16); return ++rafId; }, 'requestAnimationFrame');
G.cancelAnimationFrame = markNative(noop, 'cancelAnimationFrame');
safeDef(G, 'crypto', { value: {
    getRandomValues: markNative(arr => { for(let i=0;i<arr.length;i++)arr[i]=Math.floor(Math.random()*256);return arr; }, 'getRandomValues'),
    randomUUID: markNative(() => 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => { const r=Math.random()*16|0; return (c==='x'?r:r&0x3|0x8).toString(16); }), 'randomUUID'),
    subtle: { digest: markNative(() => Promise.resolve(new Uint8Array(32)), 'digest') },
}});
G.Image = function() { this.src=''; }; G.EventSource = function() {};
G.XMLHttpRequest = function() { this.readyState=0; this.status=0; this.responseText=''; };
XMLHttpRequest.prototype.open = function(){}; XMLHttpRequest.prototype.send = function(){ this.readyState=4; this.status=200; if(this.onreadystatechange)this.onreadystatechange(); };
G.MutationObserver = function(cb) { this.observe=noop; this.disconnect=noop; };
G.indexedDB = Object.create(null);
G._sdkGlueVersionMap = { sdkGlueVersion: '1.0.0.55', bdmsVersion: '1.0.1.7', captchaVersion: '4.0.2' };
G.URL = URL; G.URLSearchParams = URLSearchParams;
G.setTimeout = setTimeout; G.clearTimeout = clearTimeout;
G.setInterval = setInterval; G.clearInterval = clearInterval;
G.addEventListener = markNative(noop, 'addEventListener');
G.removeEventListener = markNative(noop, 'removeEventListener');
G.dispatchEvent = markNative(noop, 'dispatchEvent');
['Uint8Array','Uint16Array','Uint32Array','Int8Array','Int16Array','Int32Array','Float32Array','Float64Array','ArrayBuffer','DataView'].forEach(t => { G[t] = globalThis[t]; });

// ===== process 隐藏 =====
const rp = globalThis.process;
const fv = new Proxy(rp.versions, { get(t,p){return p==='v8'?undefined:Reflect.get(t,p);}, has(t,p){return p==='v8'?false:Reflect.has(t,p);}, ownKeys(t){return Reflect.ownKeys(t).filter(k=>k!=='v8');}, getOwnPropertyDescriptor(t,p){return p==='v8'?undefined:Reflect.getOwnPropertyDescriptor(t,p);} });
safeDef(G, 'process', { value: new Proxy(rp, { get(t,p){return p==='versions'?fv:p===Symbol.toStringTag?'Object':Reflect.get(t,p);} }) });

// ===== 验证 =====
(function() {
    const checks = [
        ['nav instanceof Navigator', G.navigator instanceof G.Navigator],
        ['doc instanceof HTMLDocument', G.document instanceof G.HTMLDocument],
        ['win instanceof Window', G instanceof G.Window],
        ['screen.colorDepth='+G.screen.colorDepth, G.screen.colorDepth === 24],
        ['localStorage.length='+G.localStorage.length, G.localStorage.length >= 5],
        ['chrome exists', !!G.chrome],
    ];
    const failed = checks.filter(c => !c[1]);
    if (failed.length) console.error('[env_full] FAILS:', failed.map(c=>c[0]).join(', '));
    else console.error('[env_full] ALL CHECKS PASSED');
})();

// ===== 完整 DOM 原型链 (EventTarget→Node→Element→HTMLElement) =====
require('./dom_prototypes.js');

// Mark DOM constructors as native
var _mkN = G.__markNative || function(f,n) {};
['EventTarget','Node','Element','HTMLElement','HTMLAnchorElement','HTMLSpanElement','HTMLCanvasElement','DOMTokenList','CanvasRenderingContext2D'].forEach(function(n) {
    var C = G[n];
    if (C) _mkN(C, n);
});

module.exports = { G, ua, noop, safeDef, markNative, setTag };
