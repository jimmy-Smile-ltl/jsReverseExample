/**
 * AST 反混淆演示脚本
 *
 * 演示如何使用 Babel AST 对典型 OB 混淆器混淆的代码进行反混淆。
 *
 * 混淆特征:
 *   - _0x 前缀的变量名
 *   - 大型字符串数组 + 索引访问
 *   - 控制流平坦化 (while + switch)
 *   - 虚假分支 / 死代码
 *
 * 本脚本包含:
 *   1. 一个模拟的 OB 混淆代码样本
 *   2. 字符串数组还原
 *   3. 常量折叠
 *   4. 死代码移除
 *
 * 用法:
 *   node ast_deobfuscate_demo.js
 *
 * 注意: search_gxb.js 本身没有被混淆，本脚本用于教学演示
 */

const parser = require("@babel/parser");
const traverse = require("@babel/traverse").default;
const generate = require("@babel/generator").default;
const t = require("@babel/types");

// ============================================================
// 模拟 OB 混淆代码样本
// ============================================================
// 这是一个简化的 OB 混淆样本，展示典型混淆模式

const obfuscatedCode = `
// 字符串数组（混淆器生成的字符串表）
var _0x4e2b = ["encrypt", "md5", "hex", "base64", "key", "sign"];

// 索引访问函数（字符串数组解引用）
function _0x2a1f(_0x3c8d) {
  return _0x4e2b[_0x3c8d - 0x1a2];
}

// 常量折叠（需要化简的表达式）
var _0x5d1c = 1 + 2 + 3 + 4 + 5;

// 实际业务代码（使用混淆后的变量名）
function _0x7f3e(_0x4a1b) {
  // 虚假分支: 永远为 true
  if (!![]) {
    var _0x1c2d = _0x2a1f(0x1a2);  // 实际是 "encrypt"
    var _0x3e4f = _0x2a1f(0x1a3);  // 实际是 "md5"
    var _0x5a6b = _0x2a1f(0x1a4);  // 实际是 "hex"
  } else {
    // 死代码: 永远不会执行
    console.log("dead code");
  }

  // 控制流平坦化（简化版 while + switch）
  var _0x7c8d = 0;
  while (!![]) {
    switch (_0x7c8d) {
      case 0:
        _0x7c8d = _0x4a1b ? 1 : 3;
        break;
      case 1:
        console.log("processing...");
        _0x7c8d = 2;
        break;
      case 2:
        return _0x1c2d + "_" + _0x3e4f + "_" + _0x5a6b;
      case 3:
        console.log("skip");
        _0x7c8d = 2;
        break;
    }
  }
}

// 调用混淆函数
var _0x9e0f = _0x7f3e(true);
console.log(_0x9e0f);
`;

console.log("=".repeat(70));
console.log("AST 反混淆演示");
console.log("=".repeat(70));
console.log();
console.log("原始混淆代码:");
console.log("-".repeat(70));
console.log(obfuscatedCode);
console.log();

// ============================================================
// 步骤 1: 解析 AST
// ============================================================
const ast = parser.parse(obfuscatedCode);

// ============================================================
// 步骤 2: 提取字符串数组
// ============================================================
console.log("步骤 1: 提取字符串数组");
console.log("-".repeat(70));

/** @type {Map<string, string[]>} */
const stringArrays = new Map();

traverse(ast, {
  VariableDeclarator(path) {
    const node = path.node;
    // 检测数组初始化
    if (t.isArrayExpression(node.init)) {
      const elements = node.init.elements;
      // 检查是否所有元素都是字符串
      if (elements.every((e) => t.isStringLiteral(e))) {
        const strings = elements.map((e) => e.value);
        const name = node.id.name;
        stringArrays.set(name, strings);
        console.log(`  发现字符串数组: ${name} (${strings.length} 个元素)`);
        strings.forEach((s, i) => {
          console.log(`    [${i}] = "${s}"`);
        });
      }
    }
  },
});

console.log();

// ============================================================
// 步骤 3: 还原字符串数组访问（替换索引为实际字符串）
// ============================================================
console.log("步骤 2: 还原字符串数组访问");
console.log("-".repeat(70));

let replaced = 0;

// 先收集字符串数组的解引用函数映射
// 如: function _0x2a1f(_0x3c8d) { return _0x4e2b[_0x3c8d - 0x1a2]; }
/** @type {Map<string, {array: string, offset: number}>} */
const derefFunctions = new Map();

traverse(ast, {
  FunctionDeclaration(path) {
    const node = path.node;
    const body = node.body.body;
    // 检测单语句 return 函数: return arrayName[param - offset]
    if (body.length === 1 && t.isReturnStatement(body[0])) {
      const arg = body[0].argument;
      if (
        t.isMemberExpression(arg) &&
        t.isIdentifier(arg.object) &&
        stringArrays.has(arg.object.name) &&
        t.isBinaryExpression(arg.property, { operator: "-" })
      ) {
        const arrayName = arg.object.name;
        const offset = arg.property.right.value;
        derefFunctions.set(node.id.name, { array: arrayName, offset });
        console.log(
          `  发现解引用函数: ${node.id.name} → ${arrayName}[idx - ${offset}]`
        );
      }
    }
  },
});

// 替换解引用函数调用为实际字符串
traverse(ast, {
  CallExpression(path) {
    const callee = path.node.callee;
    if (!t.isIdentifier(callee)) return;

    const fnInfo = derefFunctions.get(callee.name);
    if (!fnInfo) return;

    const args = path.node.arguments;
    if (args.length !== 1 || !t.isNumericLiteral(args[0])) return;

    const idx = args[0].value - fnInfo.offset;
    const strings = stringArrays.get(fnInfo.array);
    if (strings && idx >= 0 && idx < strings.length) {
      path.replaceWith(t.stringLiteral(strings[idx]));
      replaced++;
    }
  },
});

console.log(`  共替换 ${replaced} 处字符串数组访问`);
console.log();

// ============================================================
// 步骤 4: 常量折叠
// ============================================================
console.log("步骤 3: 常量折叠");
console.log("-".repeat(70));

let folded = 0;

traverse(ast, {
  BinaryExpression(path) {
    const { left, right, operator } = path.node;
    // 只处理纯数字运算
    if (
      t.isNumericLiteral(left) &&
      t.isNumericLiteral(right) &&
      ["+", "-", "*", "/", "%"].includes(operator)
    ) {
      let result;
      switch (operator) {
        case "+":
          result = left.value + right.value;
          break;
        case "-":
          result = left.value - right.value;
          break;
        case "*":
          result = left.value * right.value;
          break;
        case "/":
          result = left.value / right.value;
          break;
        case "%":
          result = left.value % right.value;
          break;
      }
      path.replaceWith(t.numericLiteral(result));
      folded++;
    }
  },
});

console.log(`  共折叠 ${folded} 个常量表达式`);
console.log();

// ============================================================
// 步骤 5: 移除死代码（永不执行的 if 分支）
// ============================================================
console.log("步骤 4: 移除死代码");
console.log("-".repeat(70));

let deadRemoved = 0;

traverse(ast, {
  IfStatement(path) {
    const test = path.node.test;

    // 检测 !![] (永远为 true 的 JS 混淆技巧)
    if (t.isUnaryExpression(test, { operator: "!" })) {
      if (t.isUnaryExpression(test.argument, { operator: "!" })) {
        const inner = test.argument.argument;
        // !![] → true
        if (t.isArrayExpression(inner) && inner.elements.length === 0) {
          path.replaceWithMultiple(path.node.consequent.body);
          deadRemoved++;
          return;
        }
        // !!{} → true
        if (t.isObjectExpression(inner) && inner.properties.length === 0) {
          path.replaceWithMultiple(path.node.consequent.body);
          deadRemoved++;
          return;
        }
      }
    }

    // 检测直接的 true/false 条件
    if (t.isBooleanLiteral(test)) {
      if (test.value) {
        path.replaceWithMultiple(path.node.consequent.body);
      } else if (path.node.alternate) {
        if (t.isBlockStatement(path.node.alternate)) {
          path.replaceWithMultiple(path.node.alternate.body);
        } else {
          path.replaceWith(path.node.alternate);
        }
      } else {
        path.remove();
      }
      deadRemoved++;
    }
  },
});

console.log(`  共移除 ${deadRemoved} 个虚假分支`);
console.log();

// ============================================================
// 输出反混淆结果
// ============================================================
console.log("=".repeat(70));
console.log("反混淆后的代码:");
console.log("=".repeat(70));
console.log();

const deobfuscated = generate(ast, {
  comments: false,
  compact: false,
}).code;

console.log(deobfuscated);
console.log();

// ============================================================
// 总结
// ============================================================
console.log("=".repeat(70));
console.log("总结");
console.log("=".repeat(70));
console.log();
console.log("  本演示展示了 OB 混淆器的主要反混淆技术:");
console.log();
console.log("  1. 字符串数组提取");
console.log("     - 找到顶层数组变量声明");
console.log("     - 解析所有字符串元素");
console.log();
console.log("  2. 字符串引用还原");
console.log("     - 识别解引用函数（如 _0x2a1f）");
console.log("     - 计算偏移量");
console.log("     - 替换函数调用为实际字符串字面量");
console.log();
console.log("  3. 常量折叠");
console.log("     - 遍历所有 BinaryExpression");
console.log("     - 计算可求值的表达式");
console.log();
console.log("  4. 死代码移除");
console.log("     - 检测永远为 true/false 的条件");
console.log("     - 移除死分支");
console.log();
console.log("  实际应用时需要根据混淆家族特征调整匹配规则。");
console.log();
console.log("  参考资源:");
console.log("    - https://astexplorer.net/");
console.log("    - https://babeljs.io/docs/babel-parser");
console.log("    - https://github.com/NXY666/Jsjiemi (解混淆工具)");
