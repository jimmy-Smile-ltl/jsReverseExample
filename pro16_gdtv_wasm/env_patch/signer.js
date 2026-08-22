/**
 * gdtv.cn WASM 签名器 — 补环境 + 扣代码 ✅
 *
 * ============================================================
 * 扣代码来源: vendor_w_b4fcb8bf.js (webpack chunk 5, 698KB)
 * 提取模块:   webpack module 266 (wasm-bindgen Rust → JS)
 *
 * 提取的核心函数调用链:
 *   B.a()                                      ← 签名入口
 *     ├── L()   passStringToWasm               ← 字符串→WASM内存
 *     ├── w.a() WASM export 'a'                ← 核心加密 (512KB .wasm)
 *     ├── G()   takeObject                     ← 从堆中取结果
 *     └── M/H   object heap / jsStack          ← wasm-bindgen ABI
 *
 *   依赖:
 *     wbg.__wbindgen_string_get ← scope 参数
 *     wbg.__wbg_getTime         ← 时间戳
 *     wbg.__wbg_getTimezoneOffset ← 时区
 *     wbg.__wbg_instanceof_Window ← 环境检测
 *     wbg.__wbg_self/window/globalThis ← 全局对象
 *     wbg.__wbg_host/origin/href ← URL 信息
 *     ... 共 30 个 wbg 导入函数
 *
 * ============================================================
 * 补方法: 30 个 wbg import 函数全部由 vendor_w.js 内部 t() 生成
 * ============================================================
 *
 * ============================================================
 * 补环境: 5 个关键补丁
 * ============================================================
 */

const fs = require("fs");
const path = require("path");

// ============================================================
// 1. 补环境: 浏览器全局对象
// ============================================================

// 1.1 Window — instanceOf 检查需要
Window = function Window() {};

// 1.2 Location — URL 信息载体
Location = function Location() {};
Location.prototype = {
    ancestorOrigins: {},
    href: "https://www.gdtv.cn/",
    origin: "https://www.gdtv.cn",
    protocol: "https:",
    host: "www.gdtv.cn",
    hostname: "www.gdtv.cn",
    port: "",
    pathname: "/",
    search: "",
    hash: "",
};

// 1.3 构建 window 对象
window = new Window();
self = window;
self.self = window;
location = new Location();
window.location = location;
document = { location: window.location };
window.document = document;

// 1.4 暴露到全局
globalThis.window = window;
globalThis.self = window;
globalThis.location = location;
globalThis.document = document;
try {
    globalThis.navigator = globalThis.navigator || {
        userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        language: "zh-CN",
        platform: "Win32",
        webdriver: false,
        cookieEnabled: true,
        onLine: true,
    };
} catch (e) { /* Node.js v24+ getter-only */ }

// 1.5 关键: 删除 global 引用 (WASM 用此检测 Node.js 环境)
delete globalThis.global;

// ============================================================
// 2. 扣代码: 从 vendor_w.js 提取 module 266
// ============================================================
const vendorCode = fs.readFileSync(path.resolve(__dirname, "..", "vendor_w.js"), "utf-8");

// 2.1 提取 WASM 二进制
const wasmMatch = vendorCode.match(/data:application\/wasm;base64,([A-Za-z0-9+/=]+)/);
if (!wasmMatch) {
    console.error("❌ 未找到 base64 WASM 数据");
    process.exit(1);
}
const wasmBytes = Buffer.from(wasmMatch[1], "base64");

// 2.2 构建假的 webpack 运行时 (避免加载全部 5 个 chunk)
const webpackModules = {};
const webpackCache = {};

function fakeWebpackRequire(id) {
    if (webpackCache[id]) return webpackCache[id].exports;
    const mod = { i: id, l: false, exports: {} };
    webpackCache[id] = mod;
    const factory = webpackModules[id];
    if (factory) factory.call(mod.exports, mod, mod.exports, fakeWebpackRequire);
    mod.l = true;
    return mod.exports;
}
fakeWebpackRequire.c = webpackCache;
fakeWebpackRequire.m = webpackModules;
fakeWebpackRequire.e = () => Promise.resolve();
fakeWebpackRequire.t = (v) => v;
fakeWebpackRequire.n = (m) => () => m;
fakeWebpackRequire.d = (e, n, g) => Object.defineProperty(e, n, { enumerable: true, get: g });
fakeWebpackRequire.o = (o, p) => Object.prototype.hasOwnProperty.call(o, p);

// 2.3 拦截 webpackJsonp.push (vendor_w.js 的加载方式)
window.webpackJsonp = [];
window.webpackJsonp.push = function (chunk) {
    const modules = chunk[1];
    for (const id of Object.keys(modules)) {
        webpackModules[id] = modules[id];
    }
};

// 2.4 提供 stub: module 266 依赖 module 43 和 147 (来自 client.js, 4.3MB)
//     这两个模块提供 Redux/Immutable 工具函数，WASM 不直接使用
webpackModules["43"] = function (m, e) { e.default = function (fn) { return fn; }; };
webpackModules["147"] = function (m, e) { e.env = {}; e.cwd = function () { return "/"; }; };

// 2.5 执行 vendor_w.js → 注册 module 266 → 调用 fakeRequire 加载
eval(vendorCode);
const B = fakeWebpackRequire("266");

// 2.6 初始化 WASM 实例
B.initSync(wasmBytes);

// ============================================================
// 3. 签名函数
// ============================================================

/**
 * 生成 gdtv.cn API 签名 headers
 *
 * @param {string} method   - HTTP 方法 ("GET" / "POST")
 * @param {string} fullUrl  - 完整 API URL
 * @param {string} deviceId - 设备 ID (格式: WEB_<uuid>)
 * @param {string} platform - 平台标识 (默认 "WEB_PC")
 * @param {string} options  - 额外选项 (默认 "")
 * @returns {object}        签名 headers 对象
 */
function sign(method, fullUrl, deviceId, platform, options) {
    const result = B.a(
        method || "GET",
        fullUrl,
        deviceId || "WEB_nodejs_00000000-0000-0000-0000-000000000001",
        platform || "WEB_PC",
        options || "",
        undefined
    );

    // B.a 返回 Map 对象 → 转为普通 Object
    const headers = {};
    if (result instanceof Map) {
        result.forEach((v, k) => { headers[k] = v; });
    } else if (Array.isArray(result)) {
        for (let i = 0; i < result.length; i += 2) {
            if (i + 1 < result.length) headers[result[i]] = result[i + 1];
        }
    }
    return headers;
}

// ============================================================
// 4. 导出
// ============================================================
module.exports = {
    sign,
    greet: () => B.greet("hello"),
    // 诊断接口
    getCaKey: () => "89541943007407288657755311868534",
    wasmBinarySize: wasmBytes.length,
};
