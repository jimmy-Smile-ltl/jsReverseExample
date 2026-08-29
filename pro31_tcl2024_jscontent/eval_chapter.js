/**
 * eval_chapter.js — 天辰文学 JS 内容加密章节的还原执行器
 *
 * 站点章节 URL 返回的是可执行 JS 代码 (而非 HTML), 执行后产生正文。
 * 原 notebook 用 js2py.eval_js(txt) 在 Python 内执行; js2py 与 Python 3.12
 * 不兼容, 本执行器改用 Node 完成同一件事 (Node 里 stub 最小 DOM 供
 * document.write / document.writeln 使用)。
 *
 * 用法:
 *   node eval_chapter.js <js文本文件或->      # 从文件读
 *   echo 'document.write("正文");' | node eval_chapter.js   # 从 stdin 读
 *
 * 输出: 还原后的正文 (每行一段)
 */

// ---- 最小 DOM stub: 把 document.write 的内容收集输出 ----
let _buf = "";
globalThis.document = {
  write(s) { _buf += String(s); },
  writeln(s) { _buf += String(s) + "\n"; },
  getElementById() { return null; },
  createElement() { return { innerHTML: "", style: {}, set innerText(v) { _buf += String(v) + "\n"; } }; },
  body: { innerHTML: "" },
};
globalThis.window = globalThis;

const fs = require("fs");

let code;
if (process.argv[2] && fs.existsSync(process.argv[2])) {
  code = fs.readFileSync(process.argv[2], "utf-8");
} else if (process.argv[2]) {
  code = process.argv[2];
} else {
  code = fs.readFileSync(0, "utf-8"); // stdin
}

// 执行密文 JS (新 Function 避免污染全局变量名冲突)
new Function("window", "document", code)(window, document);

// 输出还原正文 (段落按 <br> 切行)
process.stdout.write(_buf.replace(/<br\s*\/?>/gi, "\n") + "\n");
