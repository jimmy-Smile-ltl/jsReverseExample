/**
 * 完整 DOM 原型链 — 匹配浏览器
 * EventTarget → Node → Element → HTMLElement → HTMLAnchorElement/HTMLSpanElement/HTMLCanvasElement
 */
var noop = function() {};
var G = globalThis;

// EventTarget
G.EventTarget = function EventTarget() {};
G.EventTarget.prototype = Object.create(Object.prototype);
G.EventTarget.prototype.constructor = G.EventTarget;
G.EventTarget.prototype.addEventListener = noop;
G.EventTarget.prototype.removeEventListener = noop;
G.EventTarget.prototype.dispatchEvent = noop;

// Node
G.Node = function Node() {};
G.Node.prototype = Object.create(G.EventTarget.prototype);
G.Node.prototype.constructor = G.Node;
['nodeName','nodeType','textContent'].forEach(function(k) {
    Object.defineProperty(G.Node.prototype, k, {
        get: function() { return this['_'+k] || (k==='nodeType'?1:''); },
        set: function(v) { this['_'+k] = v; }
    });
});

// Element
G.Element = function Element() {};
G.Element.prototype = Object.create(G.Node.prototype);
G.Element.prototype.constructor = G.Element;
var ep = G.Element.prototype;
['tagName','innerHTML','outerHTML','id','className','clientWidth','clientHeight',
 'offsetWidth','offsetHeight','scrollWidth','scrollHeight'].forEach(function(k) {
    var defVal = (k==='clientWidth'||k==='clientHeight'||k==='offsetWidth'||k==='offsetHeight'||k==='scrollWidth'||k==='scrollHeight') ? 0 : '';
    Object.defineProperty(ep, k, {
        get: function() { var v = this['_'+k]; return v !== undefined ? v : defVal; },
        set: function(v) { this['_'+k] = v; },
        configurable: true
    });
});
ep.getAttribute = function(n) { return null; };
ep.setAttribute = function(n,v) {};
ep.removeAttribute = function(n) {};
ep.hasAttribute = function(n) { return false; };

// HTMLElement
G.HTMLElement = function HTMLElement() {};
G.HTMLElement.prototype = Object.create(G.Element.prototype);
G.HTMLElement.prototype.constructor = G.HTMLElement;

// HTMLAnchorElement
G.HTMLAnchorElement = function HTMLAnchorElement() {};
G.HTMLAnchorElement.prototype = Object.create(G.HTMLElement.prototype);
G.HTMLAnchorElement.prototype.constructor = G.HTMLAnchorElement;
var ap = G.HTMLAnchorElement.prototype;
['href','protocol','host','hostname','port','pathname','search','hash','origin','rel','target'].forEach(function(k) {
    var defVal = (k==='protocol') ? ':' : '';
    Object.defineProperty(ap, k, {
        get: function() { var v = this['_'+k]; return v !== undefined ? v : defVal; },
        set: function(v) { this['_'+k] = v; }
    });
});

// HTMLSpanElement
G.HTMLSpanElement = function HTMLSpanElement() {};
G.HTMLSpanElement.prototype = Object.create(G.HTMLElement.prototype);
G.HTMLSpanElement.prototype.constructor = G.HTMLSpanElement;
// span has NO href/protocol/etc — these stay undefined on span elements

// HTMLCanvasElement
G.HTMLCanvasElement = function HTMLCanvasElement() {};
G.HTMLCanvasElement.prototype = Object.create(G.HTMLElement.prototype);
G.HTMLCanvasElement.prototype.constructor = G.HTMLCanvasElement;
Object.defineProperty(G.HTMLCanvasElement.prototype, 'width', {
    get: function() { return this._width || 0; }, set: function(v) { this._width = v; }
});
Object.defineProperty(G.HTMLCanvasElement.prototype, 'height', {
    get: function() { return this._height || 0; }, set: function(v) { this._height = v; }
});
G.HTMLCanvasElement.prototype.toDataURL = function() {
    return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAARgAAAA8CAYAAABmgISf';
};
G.HTMLCanvasElement.prototype.getContext = function(type) {
    if (type === '2d') return Object.create(G.CanvasRenderingContext2D.prototype);
    return null;
};

// CanvasRenderingContext2D
G.CanvasRenderingContext2D = function CanvasRenderingContext2D() {};
G.CanvasRenderingContext2D.prototype = Object.create(Object.prototype);
G.CanvasRenderingContext2D.prototype.constructor = G.CanvasRenderingContext2D;
G.CanvasRenderingContext2D.prototype.fillText = noop;
G.CanvasRenderingContext2D.prototype.fillRect = noop;
G.CanvasRenderingContext2D.prototype.measureText = function(t) { return { width: t ? t.length * 6 : 48 }; };
G.CanvasRenderingContext2D.prototype.save = noop;
G.CanvasRenderingContext2D.prototype.restore = noop;
G.CanvasRenderingContext2D.prototype.getImageData = function() { return { data: new Uint8Array(4) }; };
Object.defineProperty(G.CanvasRenderingContext2D.prototype, 'font', { get: function() { return '10px sans-serif'; }, set: function(v) {} });
Object.defineProperty(G.CanvasRenderingContext2D.prototype, 'fillStyle', { get: function() { return '#000000'; }, set: function(v) {} });
Object.defineProperty(G.CanvasRenderingContext2D.prototype, 'strokeStyle', { get: function() { return '#000000'; }, set: function(v) {} });

// DOMTokenList — correct constructor with no href on span
G.DOMTokenList = function DOMTokenList() {};
G.DOMTokenList.prototype = Object.create(Object.prototype);
G.DOMTokenList.prototype.constructor = G.DOMTokenList;
if (G.__markNative) G.__markNative(G.DOMTokenList, 'DOMTokenList');
G.DOMTokenList.prototype.add = noop;
G.DOMTokenList.prototype.remove = noop;
G.DOMTokenList.prototype.contains = function() { return false; };
G.DOMTokenList.prototype.toggle = function() { return false; };
G.DOMTokenList.prototype.item = function() { return null; };
G.DOMTokenList.prototype.toString = function() { return ''; };
Object.defineProperty(G.DOMTokenList.prototype, 'length', { get: function() { return 0; } });
Object.defineProperty(G.DOMTokenList.prototype, 'value', { get: function() { return ''; }, set: function(v) {} });
Object.defineProperty(G.DOMTokenList.prototype, Symbol.toStringTag, { value: 'DOMTokenList' });

// All elements get a classList
Object.defineProperty(G.Element.prototype, 'classList', {
    get: function() {
        if (!this._classList) this._classList = Object.create(G.DOMTokenList.prototype);
        return this._classList;
    }
});

// ===== createElement: return correct constructor =====
var _origCE = G.document.createElement;
G.document.createElement = function(tag) {
    var t = String(tag||'div').toLowerCase();
    var el;
    if (t === 'a') el = Object.create(G.HTMLAnchorElement.prototype);
    else if (t === 'span') el = Object.create(G.HTMLSpanElement.prototype);
    else if (t === 'canvas') el = Object.create(G.HTMLCanvasElement.prototype);
    else el = Object.create(G.HTMLElement.prototype);

    el._tagName = t.toUpperCase();
    el._nodeName = t.toUpperCase();
    el._nodeType = 1;
    el._clientWidth = 0; el._clientHeight = 0;
    el._offsetWidth = 0; el._offsetHeight = 0;
    el._innerHTML = ''; el._textContent = '';
    el._id = ''; el._className = '';

    if (t === 'canvas') { el.width = 300; el.height = 150; }
    if (t === 'a') { el._href = ''; el._rel = ''; el._target = ''; }

    return el;
};
