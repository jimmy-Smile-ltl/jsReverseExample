/**
 * 酷狗定制 AES CLI (交叉验证用)
 * 用法: node kg_aes_ref.js <plaintext> [fixed_key]
 * 运行提取的 CryptoJS 原始模块 (kugou_aes_module.js, 自 kguser.v2.min.js offset 5969 提取)
 */
const fs = require('fs');
const vm = require('vm');
const path = require('path');

const aesCode = fs.readFileSync(path.join(__dirname, 'kugou_aes_module.js'), 'utf8');
const mod = { exports: {} };
const sandbox = {
    module: mod,
    exports: mod.exports,
    require: require,
    self: global,
    globalThis: global,
    console: console,
    global: global,
};
vm.runInContext(aesCode, vm.createContext(sandbox));
const AES = mod.exports;

const plaintext = process.argv[2] || '{"mobile":"13812345678"}';
const fixedKey = process.argv[3];
const result = fixedKey ? AES.encrypt(plaintext, fixedKey) : AES.encrypt(plaintext);
console.log(JSON.stringify(result));
