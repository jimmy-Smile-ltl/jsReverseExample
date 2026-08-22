// 交叉验证脚本: 用 JSDOM 实跑原 const_id.js, 捕获 window.sss 参考输出
// 用法: 把下方 SDK 路径改为本地 const_id.js 路径, npm i jsdom 后 `node verify_with_node.js`
// 输出可直接对照 main.py 的 SAMPLE_CASES
const fs = require('fs');
const { JSDOM } = require('jsdom');

const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
  url: 'https://www.sichuanair.com/',
  referrer: 'https://www.sichuanair.com/',
  userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
  contentType: 'text/html',
});
global.window = dom.window;
global.document = dom.window.document;
global.navigator = dom.window.navigator;
global.location = dom.window.location;
global.history = dom.window.history;
global.screen = dom.window.screen;
global.localStorage = dom.window.localStorage;
global.sessionStorage = dom.window.sessionStorage;
global.XMLHttpRequest = dom.window.XMLHttpRequest;
global.Image = dom.window.Image;
global.CanvasRenderingContext2D = dom.window.CanvasRenderingContext2D;
global.WebGLRenderingContext = dom.window.WebGLRenderingContext;
global.HTMLCanvasElement = dom.window.HTMLCanvasElement;
Object.defineProperty(screen, 'width', { value: 1920 });
Object.defineProperty(screen, 'height', { value: 1080 });
Object.defineProperty(navigator, 'webdriver', { value: false });
Object.defineProperty(navigator, 'plugins', { get: () => ({ length: 5 }) });
Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
Object.defineProperty(navigator, 'platform', { value: 'Win32' });

// 注意: 原 const_id.js 为第三方 SDK, 未随仓库分发; 请替换为本地路径
const SDK = '<your_local_path>/spider research/机票/pro3 四川/const_id.js';
const src = fs.readFileSync(SDK, 'utf-8');
const sdk = src.slice(
  src.indexOf('!function(r, e, t, n)'),
  src.indexOf('\nvar r = {')
);
try {
  eval(sdk);
  console.log('SDK_OK', typeof window.sss);
} catch (e) { console.log('SDK_FAIL', e.message); process.exit(1); }

// 与 main.py SAMPLE_CASES 对应的参考值 (undefined 用 {__undef:true} 占位会失真, 单独注释)
const cases = [
  ['EMPTY', ''],
  ['A', 'a'],
  ['XO', 'xOf'],
  ['TEST', 'test_1_2_3_\u8f93\u5165'],
  ['U1', '\ua44d\u0971\u095b\u09e5\u09b6\u0932\u099c\u09dc'],
  ['OBJ', { a: 1, b: 'x', c: [1, 2] }],
  ['NUM', { k: [1, -2.5, true, null], s: 'str', n: 1e21, z: 0 }],
  ['CTRL', 'a\u0001b\u001f c'],
  ['ARRU', [1, undefined, 3]],
  ['OBJ0', {}],
  ['ARR0', []],
  ['KEYO', { b: 1, a: 2, 5: 'five', 'z9': 'x' }],
  ['ESC', 'x\\n\\ty'],
];
for (const [name, input] of cases) {
  const s = window.sss(input);
  console.log(name + '=' + s + ' LEN=' + s.length);
}
