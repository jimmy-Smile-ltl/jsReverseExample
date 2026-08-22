/**
 * 拼多多 anti_content - 浏览器环境补丁 (Node.js)
 */
'use strict';


// 禁用 MessageChannel 让 React scheduler 走 setTimeout 回退
try { delete global.MessageChannel; } catch(e) {}
try { global.MessageChannel = undefined; } catch(e) {}


function setGlobal(name, value) {
  try { global[name] = value; } catch (e) {
    try { Object.defineProperty(global, name, { value, writable: true, configurable: true }); } catch (e2) {}
  }
}

const http = require('http');
const https = require('https');

class XHRPolyfill {
  constructor() {
    this.readyState = 0; this.status = 0; this.statusText = '';
    this.responseText = ''; this.response = null; this.timeout = 0;
    this.onreadystatechange = null; this.onload = null; this.onerror = null;
    this._headers = {}; this._method = 'GET'; this._url = '';
  }
  open(method, url) { this._method = method.toUpperCase(); this._url = url; this.readyState = 1; }
  setRequestHeader(name, value) { this._headers[name] = value; }
  getAllResponseHeaders() { return ''; }
  send(body) {
    try {
      const u = new URL(this._url);
      const isHttps = u.protocol === 'https:';
      (isHttps ? https : http).request({
        hostname: u.hostname, port: u.port || (isHttps ? 443 : 80),
        path: u.pathname + u.search, method: this._method,
        headers: this._headers, timeout: this.timeout || 10000,
      }, res => {
        this.status = res.statusCode; this.statusText = res.statusMessage;
        const chunks = [];
        res.on('data', c => chunks.push(c));
        res.on('end', () => {
          this.responseText = Buffer.concat(chunks).toString('utf-8');
          this.response = this.responseText;
          this.readyState = 4;
          if (this.onload) this.onload();
          if (this.onreadystatechange) this.onreadystatechange();
        });
      }).on('error', e => { if (this.onerror) this.onerror(e); }).end(body || null);
    } catch (e) {}
  }
  abort() { this.readyState = 0; }
}
setGlobal('XMLHttpRequest', XHRPolyfill);

const { TextEncoder, TextDecoder } = require('util');
setGlobal('TextEncoder', TextEncoder);
setGlobal('TextDecoder', TextDecoder);

const nav = {
  userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
  platform: 'Win32', language: 'zh-CN', languages: ['zh-CN', 'zh', 'en'],
  cookieEnabled: true, hardwareConcurrency: 8, deviceMemory: 8, maxTouchPoints: 0,
  vendor: 'Google Inc.', appCodeName: 'Mozilla', appName: 'Netscape', appVersion: '5.0',
  onLine: true, webdriver: false,
  plugins: { length: 0, refresh() {}, namedItem() { return null; }, item() { return null; } },
  mimeTypes: { length: 0, namedItem() { return null; }, item() { return null; } },
  connection: { effectiveType: '4g', rtt: 50, downlink: 10, saveData: false },
  sendBeacon() { return true; }, javaEnabled() { return false; },
};
setGlobal('navigator', nav);

setGlobal('screen', {
  width: 1920, height: 1080, availWidth: 1920, availHeight: 1040,
  colorDepth: 24, pixelDepth: 24,
  orientation: { type: 'landscape-primary', angle: 0 },
});

const loc = {
  href: 'https://www.pinduoduo.com/home/girlclothes/',
  protocol: 'https:', host: 'www.pinduoduo.com', hostname: 'www.pinduoduo.com',
  port: '', pathname: '/home/girlclothes/', search: '', hash: '',
  origin: 'https://www.pinduoduo.com',
  assign() {}, replace() {}, reload() {},
  toString() { return this.href; },
};
setGlobal('location', loc);

function mkEl(tag) {
  return {
    tagName: (tag || 'div').toUpperCase(), nodeType: 1, style: {},
    children: [], childNodes: [], attributes: {}, id: '', className: '',
    innerHTML: '', innerText: '', textContent: '',
    setAttribute(n, v) { this.attributes[n] = v; },
    getAttribute(n) { return this.attributes[n] || null; },
    removeAttribute(n) { delete this.attributes[n]; },
    appendChild(c) { this.children.push(c); this.childNodes.push(c); return c; },
    insertBefore(n) { this.children.push(n); return n; },
    addEventListener() {}, removeEventListener() {}, dispatchEvent() { return true; },
    getBoundingClientRect() { return { top: 0, left: 0, right: 1920, bottom: 947, width: 1920, height: 947 }; },
    querySelector() { return null; }, querySelectorAll() { return []; },
    getElementsByTagName() { return []; }, getElementsByClassName() { return []; },
    getElementById() { return null; },
    getContext() { return null; }, toDataURL() { return 'data:image/png;base64,'; },
  };
}

const doc = {
  cookie: '', referrer: 'https://www.pinduoduo.com/', title: '拼多多',
  location: loc, readyState: 'complete', hidden: false,
  characterSet: 'UTF-8', charset: 'UTF-8',
  documentElement: mkEl('html'), body: mkEl('body'), head: mkEl('head'),
  createElement: mkEl, createElementNS: (u, t) => mkEl(t),
  createTextNode(t) { return { textContent: t, nodeType: 3 }; },
  createDocumentFragment() { return mkEl('fragment'); },
  getElementById(id) { return id === '__next' ? mkEl('div') : null; },
  getElementsByTagName() { return []; }, getElementsByClassName() { return []; },
  querySelector() { return null; }, querySelectorAll() { return []; },
  addEventListener() {}, removeEventListener() {}, dispatchEvent() { return true; },
};
setGlobal('document', doc);

// window
const win = {
  get window() { return win; }, get self() { return win; },
  get top() { return win; }, get parent() { return win; },
  innerWidth: 1920, innerHeight: 947, outerWidth: 1920, outerHeight: 1040,
  screenX: 0, screenY: 0, pageXOffset: 0, pageYOffset: 0, scrollX: 0, scrollY: 0,
  devicePixelRatio: 1,
  navigator: nav, screen: global.screen, location: loc, document: doc,
  console: global.console,
  setTimeout: global.setTimeout, clearTimeout: global.clearTimeout,
  setInterval: global.setInterval, clearInterval: global.clearInterval,
  btoa(s) { return Buffer.from(s, 'binary').toString('base64'); },
  atob(s) { return Buffer.from(s, 'base64').toString('binary'); },
  TextEncoder, TextDecoder,
  crypto: {
    getRandomValues(buf) { for (let i = 0; i < buf.length; i++) buf[i] = Math.floor(Math.random() * 256); return buf; },
    randomUUID() { return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => { const r = Math.random() * 16 | 0; return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16); }); },
  },
  performance: {
    now() { return Date.now() - 500; },
    timing: {
      navigationStart: Date.now() - 2000, fetchStart: Date.now() - 1800,
      domainLookupStart: Date.now() - 1700, connectStart: Date.now() - 1600,
      connectEnd: Date.now() - 1500, requestStart: Date.now() - 1400,
      responseStart: Date.now() - 1000, responseEnd: Date.now() - 800,
      domLoading: Date.now() - 700, domInteractive: Date.now() - 500,
      domContentLoadedEventStart: Date.now() - 400,
      domContentLoadedEventEnd: Date.now() - 300, domComplete: Date.now() - 200,
      loadEventStart: Date.now() - 100, loadEventEnd: Date.now(),
    },
    getEntriesByType() { return []; }, mark() {}, measure() {},
  },
  requestAnimationFrame(cb) { return setTimeout(() => cb(Date.now()), 16); },
  cancelAnimationFrame(id) { clearTimeout(id); },
  addEventListener() {}, removeEventListener() {}, dispatchEvent(e) { return true; },
  getComputedStyle() { return { getPropertyValue() { return ''; } }; },
  matchMedia() { return { matches: false, media: '', addListener() {}, removeListener() {} }; },
  open() { return {}; }, close() {}, focus() {}, blur() {},
  scrollTo() {}, scrollBy() {}, scroll() {},
  postMessage() {}, getSelection() { return { toString() { return ''; } }; },
  localStorage: (() => { var s = {}; return { get length() { return Object.keys(s).length; }, getItem(k) { return s.hasOwnProperty(k) ? s[k] : null; }, setItem(k, v) { s[k] = String(v); }, removeItem(k) { delete s[k]; }, clear() { for (var k in s) delete s[k]; } }; })(),
  sessionStorage: (() => { var s = {}; return { get length() { return Object.keys(s).length; }, getItem(k) { return s.hasOwnProperty(k) ? s[k] : null; }, setItem(k, v) { s[k] = String(v); }, removeItem(k) { delete s[k]; }, clear() { for (var k in s) delete s[k]; } }; })(),
  history: { length: 1, pushState() {}, replaceState() {}, back() {}, forward() {}, go() {} },
  name: '', closed: false,
  webpackJsonp: [],
};

// Add standard globals to window (fbeZ may access them via window.XXX)
win.Date = global.Date;
win.Math = global.Math;
win.Object = global.Object;
win.Array = global.Array;
win.String = global.String;
win.Number = global.Number;
win.Boolean = global.Boolean;
win.RegExp = global.RegExp;
win.Error = global.Error;
win.JSON = global.JSON;
win.parseInt = global.parseInt;
win.parseFloat = global.parseFloat;
win.isNaN = global.isNaN;
win.isFinite = global.isFinite;
win.encodeURIComponent = global.encodeURIComponent;
win.decodeURIComponent = global.decodeURIComponent;

setGlobal('window', win);
setGlobal('self', win);

setGlobal('Image', class Image { constructor(w, h) { this.width = w || 0; this.height = h || 0; this.src = ''; this.onload = null; this.onerror = null; this.complete = false; } });
setGlobal('HTMLElement', class HTMLElement {});

if (typeof global.URL === 'undefined') setGlobal('URL', require('url').URL);

console.log('[env] done');

// MutationObserver (React scheduler needs this)
setGlobal('MutationObserver', class MutationObserver {
  constructor(cb) { this._cb = cb; }
  observe(target, options) {}
  disconnect() {}
  takeRecords() { return []; }
});

// ============================================================