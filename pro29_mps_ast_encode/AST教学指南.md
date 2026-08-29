# AST 逆向教学指南 —— 从入门到实战

> 本指南教你使用 **Babel AST**（Abstract Syntax Tree，抽象语法树）进行 JavaScript 逆向分析。
> 以本项目（公安部网站）的真实代码为案例，手把手带你从零开始掌握 AST 技术。

---

## 目录

1. [为什么需要 AST？](#一为什么需要-ast)
2. [环境搭建](#二环境搭建)
3. [第一个 AST 程序：解析 JS 代码](#三第一个-ast-程序解析-js-代码)
4. [AST 节点类型速查](#四ast-节点类型速查)
5. [核心 API：traverse（遍历）](#五核心-apitraverse遍历)
6. [核心 API：增删改查节点](#六核心-api增删改查节点)
7. [实战 1：提取函数列表](#七实战-1提取函数列表)
8. [实战 2：识别混淆类型](#八实战-2识别混淆类型)
9. [实战 3：OB 混淆 — 字符串数组还原](#九实战-3ob-混淆--字符串数组还原)
10. [实战 4：OB 混淆 — 常量折叠](#十实战-4ob-混淆--常量折叠)
11. [实战 5：OB 混淆 — 死代码移除](#十一实战-5ob-混淆--死代码移除)
12. [实战 6：控制流平坦化还原](#十二实战-6控制流平坦化还原)
13. [实战 7：自执行函数解密](#十三实战-7自执行函数解密)
14. [高级技巧](#十四高级技巧)
15. [常见问题与调试](#十五常见问题与调试)
16. [练习清单](#十六练习清单)

---

## 一、为什么需要 AST？

### 1.1 什么是 AST？

```
源代码                        AST (抽象语法树)               可执行代码
──────────                    ──────────────────             ──────────
var x = 1 + 2;    ──parse──>  VariableDeclaration    ──generate──>  var x = 3;
                               ├── VariableDeclarator
                               │   ├── Identifier (x)
                               │   └── BinaryExpression (+)
                               │       ├── NumericLiteral (1)
                               │       └── NumericLiteral (2)
```

**AST 是源代码的结构化表示**。它把代码字符串变成一棵树，每个节点代表一个语法结构。

### 1.2 为什么 JS 逆向需要 AST？

| 传统方法（正则/字符串替换） | AST 方法 |
|---|---|
| `code.replace(/_0x1234/g, 'md5')` | 遍历所有 `Identifier` 节点，按作用域精确替换 |
| 无法处理嵌套结构 | 完整理解代码结构 |
| 正则匹配容易出错 | 语法级精确操作 |
| 只能做简单替换 | 可以重构整个代码结构 |

**核心优势**：AST 让你可以像编译器一样理解和修改 JavaScript 代码。

### 1.3 AST 在逆向中的应用场景

```
混淆代码 → [AST 解析] → [遍历/分析] → [节点替换] → [代码生成] → 可读代码
                                    ↓
                            • 提取字符串数组
                            • 替换索引访问
                            • 折叠常量表达式
                            • 移除死代码
                            • 还原控制流
                            • 重命名变量
```

---

## 二、环境搭建

### 2.1 安装依赖

```bash
npm install @babel/parser @babel/traverse @babel/generator @babel/types
```

四个包的作用：

| 包 | 作用 | 类比 |
|---|---|---|
| `@babel/parser` | 把 JS 代码字符串解析成 AST | `.py` → AST |
| `@babel/traverse` | 遍历 AST 树，访问/修改节点 | AST 的 for 循环 |
| `@babel/generator` | 把修改后的 AST 生成回 JS 代码 | AST → `.py` |
| `@babel/types` | 创建/检查/断言 AST 节点 | 节点的工厂函数 |

### 2.2 最小可运行示例

创建 `demo_hello_ast.js`：

```javascript
// 1. 引入
const parser = require("@babel/parser");
const traverse = require("@babel/traverse").default;
const generate = require("@babel/generator").default;
const t = require("@babel/types");

// 2. 源代码
const code = `var x = 1 + 2;`;

// 3. 解析 → AST
const ast = parser.parse(code);

// 4. 打印顶层节点
console.log("顶层语句数:", ast.program.body.length);
console.log("第一个节点类型:", ast.program.body[0].type);
// 输出: VariableDeclaration

// 5. 生成回代码
const output = generate(ast).code;
console.log("生成的代码:", output);
// 输出: var x = 1 + 2;
```

运行：`node demo_hello_ast.js`

### 2.3 在线工具

**强烈推荐** [AST Explorer](https://astexplorer.net/)：
- 左边贴 JS 代码，右边实时显示 AST 树
- 可选择 `@babel/parser` 作为解析器
- **学习 AST 的最佳工具**，建议边看本文边在 AST Explorer 里实验

---

## 三、第一个 AST 程序：解析 JS 代码

### 3.1 解析选项

```javascript
const ast = parser.parse(code, {
  sourceType: "script",    // "script" | "module" | "unambiguous"
  plugins: [],              // 语法插件，如 "jsx", "typescript"
  errorRecovery: true,      // 遇到语法错误是否继续（混淆代码常用）
});
```

### 3.2 理解 AST 结构

每种 JS 语法都有对应的 AST 节点类型。以下是一段代码和它的 AST 结构：

```javascript
// === 源代码 ===
function add(a, b) {
  return a + b;
}
var result = add(1, 2);
```

```
// === AST 树结构（简化）===
Program                          ← 根节点
├── FunctionDeclaration          ← function add(a, b) {...}
│   ├── id: Identifier("add")    ← 函数名
│   ├── params:                  ← 参数列表
│   │   ├── Identifier("a")
│   │   └── Identifier("b")
│   └── body: BlockStatement     ← 函数体
│       └── ReturnStatement      ← return 语句
│           └── BinaryExpression ← a + b
│               ├── Identifier("a")
│               ├── operator: "+"
│               └── Identifier("b")
└── VariableDeclaration          ← var result = add(1, 2);
    └── VariableDeclarator
        ├── id: Identifier("result")
        └── init: CallExpression ← add(1, 2)
            ├── callee: Identifier("add")
            └── arguments:
                ├── NumericLiteral(1)
                └── NumericLiteral(2)
```

### 3.3 动手实验

在 AST Explorer 中粘贴下面代码，观察 AST 结构：

```javascript
// 实验 1: 不同字面量
var a = "hello";        // → StringLiteral
var b = 123;            // → NumericLiteral
var c = true;           // → BooleanLiteral
var d = null;           // → NullLiteral

// 实验 2: 不同表达式
var e = a + b;          // → BinaryExpression
var f = !a;             // → UnaryExpression
var g = obj.prop;       // → MemberExpression
var h = arr[0];         // → MemberExpression (computed: true)
var i = foo(1, 2);      // → CallExpression

// 实验 3: 混淆常见模式
var j = !![];           // → UnaryExpression(!) → UnaryExpression(!) → ArrayExpression
var k = "a" + "b";      // → BinaryExpression (两个 StringLiteral)
```

---

## 四、AST 节点类型速查

### 4.1 节点分类

#### 📦 **声明类**（Declaration）

| 节点类型 | JS 代码 | AST Explorer 验证 |
|---|---|---|
| `VariableDeclaration` | `var x = 1;` | `declarations[0].init` |
| `FunctionDeclaration` | `function f(){}` | `id.name` = "f" |
| `VariableDeclarator` | `x = 1` (等号两边) | `id` + `init` |

#### 📝 **语句类**（Statement）

| 节点类型 | JS 代码 | 关键属性 |
|---|---|---|
| `ExpressionStatement` | `foo();` | `expression` |
| `BlockStatement` | `{ ... }` | `body[]` |
| `ReturnStatement` | `return x;` | `argument` |
| `IfStatement` | `if(x){}else{}` | `test`, `consequent`, `alternate` |
| `ForStatement` | `for(;;){}` | `init`, `test`, `update`, `body` |
| `WhileStatement` | `while(x){}` | `test`, `body` |
| `SwitchStatement` | `switch(x){case...}` | `discriminant`, `cases[]` |
| `SwitchCase` | `case 1:` | `test`, `consequent[]` |

#### 🧮 **表达式类**（Expression）

| 节点类型 | JS 代码 | 关键属性 |
|---|---|---|
| `Identifier` | `myVar` | `name` |
| `NumericLiteral` | `123` | `value` |
| `StringLiteral` | `"hello"` | `value` |
| `BooleanLiteral` | `true/false` | `value` |
| `BinaryExpression` | `a + b` | `left`, `operator`, `right` |
| `UnaryExpression` | `!a`, `typeof a` | `operator`, `argument` |
| `CallExpression` | `foo(1,2)` | `callee`, `arguments[]` |
| `MemberExpression` | `obj.prop` / `obj["prop"]` | `object`, `property`, `computed` |
| `ArrayExpression` | `[1,2,3]` | `elements[]` |
| `ObjectExpression` | `{a:1}` | `properties[]` |
| `AssignmentExpression` | `x = 1` | `left`, `operator`, `right` |
| `ConditionalExpression` | `a ? b : c` | `test`, `consequent`, `alternate` |
| `LogicalExpression` | `a && b`, `a \|\| b` | `left`, `operator`, `right` |
| `SequenceExpression` | `(a, b, c)` | `expressions[]` |
| `TemplateLiteral` | `` `hello ${name}` `` | `quasis[]`, `expressions[]` |

### 4.2 如何查看节点类型？

```javascript
// 方法 1: 在代码中打印
traverse(ast, {
  enter(path) {
    console.log(path.node.type);  // 打印每个节点的类型
  }
});

// 方法 2: 使用 AST Explorer 在线查看
// https://astexplorer.net/
```

### 4.3 节点判断的三种写法

```javascript
// 写法 1: visitor 属性名（推荐，最简洁）
traverse(ast, {
  StringLiteral(path) { /* 只处理 StringLiteral */ },
  NumericLiteral(path) { /* 只处理 NumericLiteral */ },
});

// 写法 2: 条件判断
traverse(ast, {
  enter(path) {
    if (path.node.type === "StringLiteral") { /* ... */ }
    if (path.node.type === "CallExpression") { /* ... */ }
  }
});

// 写法 3: 使用 @babel/types 断言（类型安全）
if (t.isStringLiteral(path.node)) { /* ... */ }
if (t.isCallExpression(path.node)) { /* ... */ }
if (t.isIdentifier(path.node, { name: "eval" })) { /* ... */ }
```

---

## 五、核心 API：traverse（遍历）

### 5.1 Visitor 模式

`traverse` 使用**访问者模式**：你告诉它"当遇到 X 类型的节点时，调用这个函数"。

```javascript
traverse(ast, {
  // 访问者函数名 = 节点类型
  Identifier(path) {
    console.log("发现标识符:", path.node.name);
  },

  // 也可以同时定义进入和退出
  CallExpression: {
    enter(path) {
      console.log("进入函数调用:", path.node.callee.name);
    },
    exit(path) {
      console.log("离开函数调用");
    }
  }
});
```

### 5.2 Path（路径）对象

`path` 是 traverse 给每个访问者的参数，它比 `node` 多了一层上下文：

| 属性/方法 | 说明 | 示例 |
|---|---|---|
| `path.node` | 当前 AST 节点 | `path.node.type` |
| `path.parent` | 父节点 | `path.parent.type` |
| `path.parentPath` | 父路径 | `path.parentPath.node` |
| `path.scope` | 作用域信息 | `path.scope.getBinding('x')` |
| `path.replaceWith(node)` | 替换当前节点 | 见下文 |
| `path.remove()` | 删除当前节点 | 见下文 |
| `path.insertBefore(node)` | 在前面插入 | 见下文 |
| `path.insertAfter(node)` | 在后面插入 | 见下文 |
| `path.skip()` | 跳过子节点遍历 | 性能优化 |
| `path.stop()` | 停止整个遍历 | 提前终止 |
| `path.traverse(visitor)` | 从当前节点开始子遍历 | 局部遍历 |

### 5.3 path 与 node 的区别

```javascript
traverse(ast, {
  Identifier(path) {
    // path.node:    当前 Identifier 节点
    // path.parent:  父节点（可能是 VariableDeclarator）
    // path.parentPath.node: 同上

    // 要替换的是 path，不是 node！
    path.replaceWith(t.identifier("newName"));
    // ✅ 正确：替换整个路径

    // path.node.name = "newName";
    // ⚠️ 只改了 node 属性，但没触发 AST 更新
  }
});
```

### 5.4 遍历顺序

```
Program
  enter → FunctionDeclaration enter → Identifier("add") enter/exit → ...
       → FunctionDeclaration exit
       → VariableDeclaration enter → ...
       → VariableDeclaration exit
  exit
```

**enter** 先访问父节点再访问子节点
**exit** 先访问子节点再访问父节点（适合需要子节点信息后才能操作父节点的场景）

---

## 六、核心 API：增删改查节点

### 6.1 替换节点 `path.replaceWith()`

```javascript
// 示例：把所有数字 1 替换成 999
traverse(ast, {
  NumericLiteral(path) {
    if (path.node.value === 1) {
      path.replaceWith(t.numericLiteral(999));
    }
  }
});
// var x = 1 + 2;  →  var x = 999 + 2;
```

### 6.2 删除节点 `path.remove()`

```javascript
// 示例：删除所有 console.log 语句
traverse(ast, {
  CallExpression(path) {
    if (
      t.isMemberExpression(path.node.callee) &&
      t.isIdentifier(path.node.callee.object, { name: "console" }) &&
      t.isIdentifier(path.node.callee.property, { name: "log" })
    ) {
      // 如果 console.log 是 ExpressionStatement，删除整条语句
      if (t.isExpressionStatement(path.parent)) {
        path.parentPath.remove();
      }
    }
  }
});
// console.log("hello"); → (被删除)
```

### 6.3 插入节点

```javascript
// 示例：在每个 return 之前插入 console.log
traverse(ast, {
  ReturnStatement(path) {
    const logStatement = t.expressionStatement(
      t.callExpression(
        t.memberExpression(t.identifier("console"), t.identifier("log")),
        [t.stringLiteral("return called")]
      )
    );
    path.insertBefore(logStatement);
  }
});
```

### 6.4 替换为多个节点 `path.replaceWithMultiple()`

```javascript
// 示例：把 a ? b : c 展开为 if-else
traverse(ast, {
  ConditionalExpression(path) {
    if (t.isExpressionStatement(path.parent)) {
      // 三元表达式 → if-else
      const ifStatement = t.ifStatement(
        path.node.test,
        t.blockStatement([t.expressionStatement(path.node.consequent)]),
        t.blockStatement([t.expressionStatement(path.node.alternate)])
      );
      path.parentPath.replaceWith(ifStatement);
    }
  }
});
```

### 6.5 使用 @babel/types 创建节点

```javascript
const t = require("@babel/types");

// 字面量
t.numericLiteral(123)          // 123
t.stringLiteral("hello")       // "hello"
t.booleanLiteral(true)         // true
t.nullLiteral()                // null

// 标识符
t.identifier("myVar")          // myVar

// 表达式
t.binaryExpression("+", left, right)     // left + right
t.unaryExpression("!", arg)              // !arg
t.callExpression(callee, args)           // callee(args)
t.memberExpression(obj, prop)            // obj.prop
t.memberExpression(obj, prop, true)      // obj[prop]

// 语句
t.expressionStatement(expr)              // expr;
t.returnStatement(arg)                   // return arg;
t.ifStatement(test, cons, alt)           // if(test) cons; else alt;
t.blockStatement(body)                   // { body }
t.variableDeclaration("var", [decl])     // var decl;
t.variableDeclarator(id, init)           // id = init

// 函数
t.functionDeclaration(id, params, body)  // function id(params) { body }
```

> 完整列表见 [Babel Types 文档](https://babeljs.io/docs/babel-types)

---

## 七、实战 1：提取函数列表

### 目标

从 `search_gxb.js`（49KB，56个函数）中提取所有函数名、参数、位置。

> 本项目的 `ast_extract.js` 就是完整的实现，这里拆解其核心逻辑。

### 步骤 1：解析文件

```javascript
const fs = require("fs");
const parser = require("@babel/parser");

const code = fs.readFileSync("./search_gxb.js", "utf-8");
const ast = parser.parse(code, { sourceType: "script" });
```

### 步骤 2：遍历找出所有 FunctionDeclaration

```javascript
const traverse = require("@babel/traverse").default;

const functions = [];

traverse(ast, {
  FunctionDeclaration(path) {
    const node = path.node;
    functions.push({
      name: node.id ? node.id.name : "<anonymous>",
      params: node.params.map(p => p.name),
      line: node.loc.start.line,          // 起始行号
      statements: node.body.body.length,   // 函数体语句数
    });
  }
});
```

### 步骤 3：分类展示

```javascript
// 按语句数排序，找出最复杂的函数
functions.sort((a, b) => b.statements - a.statements);
console.log("最复杂的 5 个函数:");
functions.slice(0, 5).forEach(fn => {
  console.log(`  ${fn.name}(${fn.params.join(",")}) — ${fn.statements} 条语句`);
});
```

**输出示例**：
```
最复杂的 5 个函数:
  goPage(toPage,t3) — 29 条语句
  html2txt(str,noEnter) — 27 条语句
  checkAll(form) — 18 条语句
  printText(condition) — 14 条语句
  txt(str,len,suffix) — 11 条语句
```

### 步骤 4：分析调用关系（进阶）

```javascript
const callGraph = new Map();

traverse(ast, {
  FunctionDeclaration(path) {
    const caller = path.node.id.name;
    const called = [];

    path.traverse({
      CallExpression(innerPath) {
        if (t.isIdentifier(innerPath.node.callee)) {
          called.push(innerPath.node.callee.name);
        }
      }
    });

    callGraph.set(caller, called);
  }
});

// 打印调用图
for (const [caller, called] of callGraph) {
  if (called.length > 0) {
    console.log(`  ${caller} 调用 → ${[...new Set(called)].join(", ")}`);
  }
}
```

**输出示例**：
```
  goPage 调用 → addOrUpdateCookie, encodeURIComponent, goPage
  c 调用 → addOrUpdateCookie, encodeURIComponent, Image
  u 调用 → encodeURIComponent, encode64
```

### 小结

| 学到的技术 | 对应 API |
|---|---|
| 解析文件 | `parser.parse(code)` |
| 遍历特定节点 | `traverse(ast, { FunctionDeclaration(path){} })` |
| 获取节点信息 | `node.id.name`, `node.params`, `node.loc` |
| 子遍历 | `path.traverse({...})` |
| 作用域 | `path.scope.getBinding(name)` |

---

## 八、实战 2：识别混淆类型

### 8.1 自动识别脚本

在对一个目标站点动手之前，先用这个脚本快速判断混淆类型：

```javascript
function detectObfuscation(code) {
  const result = {
    hasOBfuscator: false,      // _0x 变量
    hasStringArray: false,     // 大型字符串数组
    hasControlFlow: false,     // while+switch
    hasEvalChain: false,       // 多层 eval
    hasWasm: false,            // WebAssembly
    hasJSVMP: false,           // 自定义 VM
    suspiciousPatterns: [],
  };

  // 1. OB 混淆器特征: _0x 前缀变量
  const obVars = code.match(/_0x[0-9a-fA-F]+/g);
  if (obVars && obVars.length > 10) {
    result.hasOBfuscator = true;
    result.suspiciousPatterns.push(`OB 混淆器: ${obVars.length} 个 _0x 变量`);
  }

  // 2. 大型字符串数组
  const arrMatch = code.match(/var\s+(\w+)\s*=\s*\[([^\]]{500,})\]/);
  if (arrMatch) {
    result.hasStringArray = true;
    result.suspiciousPatterns.push(`字符串数组: ${arrMatch[1]}`);
  }

  // 3. 控制流平坦化: while(true) + switch
  if (code.includes("while(true)") || code.includes("while (true)")) {
    if (code.includes("switch")) {
      result.hasControlFlow = true;
      result.suspiciousPatterns.push("控制流平坦化: while+switch");
    }
  }

  // 4. 多层 eval
  const evalCount = (code.match(/eval\(/g) || []).length;
  if (evalCount > 5) {
    result.hasEvalChain = true;
    result.suspiciousPatterns.push(`多层 eval: ${evalCount} 处`);
  }

  // 5. WebAssembly
  if (code.includes("WebAssembly") || code.includes("wasm")) {
    result.hasWasm = true;
    result.suspiciousPatterns.push("WebAssembly");
  }

  // 6. VM 保护: 大型数字数组 + 解释器循环
  const bigArray = code.match(/var\s+\w+\s*=\s*\[(\d+,){100,}/);
  if (bigArray) {
    result.hasJSVMP = true;
    result.suspiciousPatterns.push("JSVMP: 大型数字数组");
  }

  return result;
}
```

### 8.2 各混淆类型的处理策略

| 混淆类型 | 特征 | 处理策略 | 难度 |
|---|---|---|---|
| **OB 混淆器** | `_0x` 前缀变量、字符串数组 | 提取字符串表 → 替换引用 | ⭐⭐ |
| **sojson** | `jsjiami.com` 标记、多层 eval | 解 eval 层 → 字符串还原 | ⭐⭐⭐ |
| **控制流平坦化** | `while(true)` + `switch` | 分析分发器 → 按序重组代码块 | ⭐⭐⭐⭐ |
| **JSVMP** | 自定义字节码数组 + 解释器 | 提取操作码映射 → 反汇编 → 逻辑还原 | ⭐⭐⭐⭐⭐ |
| **WASM** | `WebAssembly.instantiate` | 导出 wasm → wasm2wat → 分析 | ⭐⭐⭐⭐ |
| **JSoo** | 内存数组移位混淆 | 快照数组初始状态 → 替换 | ⭐⭐⭐ |

---

## 九、实战 3：OB 混淆 — 字符串数组还原

### 9.1 混淆原理

OB 混淆器（obfuscator.io）把代码中的字符串提取到一个数组中，然后用索引访问：

```javascript
// === 混淆前 ===
var algorithm = "md5";
var encoding = "hex";

// === 混淆后 ===
var _0x4e2b = ["md5", "hex", "base64"];           // 字符串数组
var algorithm = _0x4e2b[0];                        // 索引访问
var encoding = _0x4e2b[1];
```

更复杂的情况，有一个解引用函数：

```javascript
var _0x4e2b = ["md5", "hex", "base64"];

// 偏移量让索引不是从 0 开始
function _0x2a1f(_0x3c8d) {
  return _0x4e2b[_0x3c8d - 0x1a2];   // _0x3c8d - 418
}

var algorithm = _0x2a1f(0x1a2);       // → _0x4e2b[0] → "md5"
var encoding = _0x2a1f(0x1a3);        // → _0x4e2b[1] → "hex"
```

### 9.2 还原策略

```
步骤 1: 找到字符串数组 var _0x4e2b = ["md5", "hex", ...]
  ↓
步骤 2: 找到解引用函数 function _0x2a1f(x) { return _0x4e2b[x - 418]; }
  ↓               提取: 数组名= _0x4e2b, 偏移量= 418
  ↓
步骤 3: 遍历所有 CallExpression，检查是否是解引用函数调用
  ↓    _0x2a1f(0x1a2) → 索引=0x1a2-418=0 → "md5"
  ↓    替换为 StringLiteral("md5")
  ↓
步骤 4: 删除字符串数组和解引用函数（可选）
  ↓
结果: var algorithm = "md5";
```

### 9.3 完整实现

```javascript
function restoreStringArray(ast) {
  // ===== 步骤 1: 找到所有顶层字符串数组 =====
  const stringArrays = new Map();

  traverse(ast, {
    VariableDeclarator(path) {
      const node = path.node;
      // 只处理顶层数组: var xxx = ["a", "b", ...]
      if (
        t.isArrayExpression(node.init) &&
        node.init.elements.length > 3 &&               // 至少 3 个元素
        node.init.elements.every(e => t.isStringLiteral(e))  // 全是字符串
      ) {
        const strings = node.init.elements.map(e => e.value);
        stringArrays.set(node.id.name, strings);
        console.log(`[+] 发现字符串数组: ${node.id.name} (${strings.length}个)`);
      }
    }
  });

  // ===== 步骤 2: 找到解引用函数 =====
  const derefMap = new Map();  // name → {array, offset}

  traverse(ast, {
    FunctionDeclaration(path) {
      const body = path.node.body.body;
      // 检测单语句函数: return arrayName[param - offset]
      if (body.length === 1 && t.isReturnStatement(body[0])) {
        const arg = body[0].argument;
        if (
          t.isMemberExpression(arg) &&
          t.isIdentifier(arg.object) &&           // arrayName
          stringArrays.has(arg.object.name) &&     // 是已知字符串数组
          t.isBinaryExpression(arg.property, { operator: "-" }) &&
          t.isIdentifier(arg.property.left) &&     // param (和第1个参数同名)
          t.isNumericLiteral(arg.property.right)   // 偏移量
        ) {
          const array = arg.object.name;
          const offset = arg.property.right.value;
          derefMap.set(path.node.id.name, { array, offset });
          console.log(`[+] 解引用函数: ${path.node.id.name}(x) → ${array}[x - ${offset}]`);
        }
      }
    }
  });

  // ===== 步骤 3: 替换解引用调用 =====
  let replaced = 0;

  traverse(ast, {
    CallExpression(path) {
      if (!t.isIdentifier(path.node.callee)) return;

      const info = derefMap.get(path.node.callee.name);
      if (!info) return;

      const args = path.node.arguments;
      if (args.length < 1 || !t.isNumericLiteral(args[0])) return;

      const idx = args[0].value - info.offset;
      const strings = stringArrays.get(info.array);

      if (strings && idx >= 0 && idx < strings.length) {
        path.replaceWith(t.stringLiteral(strings[idx]));
        replaced++;
      }
    }
  });

  console.log(`[+] 替换了 ${replaced} 处字符串引用`);
}
```

### 9.4 练习

用 AST Explorer 分析以下混淆代码，然后写还原脚本：

```javascript
var _0xabc = ["hello", "world", "foo", "bar"];
function _0xdef(x) {
  return _0xabc[x - 100];
}
var a = _0xdef(100);
var b = _0xdef(101);
console.log(a + " " + b);
```

---

## 十、实战 4：OB 混淆 — 常量折叠

### 10.1 混淆原理

OB 混淆器把简单的常量计算拆成多步，增加阅读难度：

```javascript
// === 混淆前 ===
var x = 15;

// === 混淆后（各种等价变形）===
var x = 1 + 2 + 3 + 4 + 5;          // 连续加法
var y = 0x10;                        // 十六进制
var z = 2 * 8;                       // 乘法
var w = parseInt("42");              // 字符串转数字
```

### 10.2 还原策略

遍历所有 `BinaryExpression`，如果左右都是 `NumericLiteral`，直接计算结果：

```javascript
function constantFolding(ast) {
  let folded = 0;

  traverse(ast, {
    BinaryExpression(path) {
      const { left, right, operator } = path.node;

      // 只处理两个操作数都是数字的情况
      if (!t.isNumericLiteral(left) || !t.isNumericLiteral(right)) return;

      let result;
      switch (operator) {
        case "+":  result = left.value + right.value; break;
        case "-":  result = left.value - right.value; break;
        case "*":  result = left.value * right.value; break;
        case "/":  result = left.value / right.value; break;
        case "%":  result = left.value % right.value; break;
        case "**": result = left.value ** right.value; break;
        default: return;  // 不支持的运算符
      }

      path.replaceWith(t.numericLiteral(result));
      folded++;
    }
  });

  console.log(`[+] 折叠了 ${folded} 个常量表达式`);
}
```

### 10.3 需要多趟遍历的情况

```javascript
// 单趟遍历: 1+2+3+4+5 → 3+3+4+5 (只折叠了第一对)
// 需要多次遍历直到没有新的折叠

function constantFoldingFull(ast) {
  let totalFolded = 0;
  let folded;

  do {
    folded = 0;
    traverse(ast, {
      BinaryExpression(path) {
        const { left, right, operator } = path.node;
        if (t.isNumericLiteral(left) && t.isNumericLiteral(right)) {
          let result;
          switch (operator) {
            case "+": result = left.value + right.value; break;
            case "-": result = left.value - right.value; break;
            case "*": result = left.value * right.value; break;
            case "/": result = left.value / right.value; break;
          }
          path.replaceWith(t.numericLiteral(result));
          folded++;
        }
      }
    });
    totalFolded += folded;
  } while (folded > 0);  // 继续直到没有更多可折叠的

  console.log(`[+] 共折叠 ${totalFolded} 个常量`);
}
```

### 10.4 也包括字符串拼接

```javascript
traverse(ast, {
  BinaryExpression(path) {
    const { left, right, operator } = path.node;

    // 字符串拼接: "a" + "b" → "ab"
    if (operator === "+" && t.isStringLiteral(left) && t.isStringLiteral(right)) {
      path.replaceWith(t.stringLiteral(left.value + right.value));
    }
  }
});
```

---

## 十一、实战 5：OB 混淆 — 死代码移除

### 11.1 混淆原理

OB 混淆器插入永不执行的分支，迷惑分析者：

```javascript
// 永远为 true 的条件（JS 混淆常用技巧）
if (!![]) {           // !![] → true
  // 真实代码
} else {
  // 永远不会执行的死代码
}

if ("a" !== "b") {    // 永远为 true
  // 真实代码
}

if (true) {
  var x = 1;           // 真实代码
} else {
  deadCode();           // 死代码
}
```

### 11.2 还原策略

识别永远为 true/false 的条件表达式，移除死分支：

```javascript
function removeDeadCode(ast) {
  let removed = 0;

  traverse(ast, {
    IfStatement(path) {
      const test = path.node.test;

      // ===== 模式 1: 直接 true/false =====
      if (t.isBooleanLiteral(test)) {
        if (test.value) {
          // if (true) { ... } else { dead }
          path.replaceWithMultiple(
            t.isBlockStatement(path.node.consequent)
              ? path.node.consequent.body
              : [path.node.consequent]
          );
        } else {
          // if (false) { dead } else { ... }
          if (path.node.alternate) {
            path.replaceWithMultiple(
              t.isBlockStatement(path.node.alternate)
                ? path.node.alternate.body
                : [path.node.alternate]
            );
          } else {
            path.remove();
          }
        }
        removed++;
        return;
      }

      // ===== 模式 2: !![] → true =====
      if (isAlwaysTrue(test)) {
        path.replaceWithMultiple(
          t.isBlockStatement(path.node.consequent)
            ? path.node.consequent.body
            : [path.node.consequent]
        );
        removed++;
        return;
      }

      // ===== 模式 3: ![] → false =====
      if (isAlwaysFalse(test)) {
        if (path.node.alternate) {
          path.replaceWithMultiple(
            t.isBlockStatement(path.node.alternate)
              ? path.node.alternate.body
              : [path.node.alternate]
          );
        } else {
          path.remove();
        }
        removed++;
      }
    }
  });

  console.log(`[+] 移除了 ${removed} 个死分支`);
}

function isAlwaysTrue(node) {
  // !![] → true,  !0 → true,  "x" !== "y" → true
  if (t.isUnaryExpression(node, { operator: "!" })) {
    if (t.isUnaryExpression(node.argument, { operator: "!" })) {
      return true;  // !!anything → true (在 JS 混淆中)
    }
    if (t.isNumericLiteral(node.argument, { value: 0 })) {
      return true;  // !0 → true
    }
  }
  if (
    t.isBinaryExpression(node, { operator: "!==" }) &&
    t.isStringLiteral(node.left) &&
    t.isStringLiteral(node.right) &&
    node.left.value !== node.right.value
  ) {
    return true;  // "a" !== "b" → true
  }
  return false;
}

function isAlwaysFalse(node) {
  // ![] → false,  !1 → false,  "x" === "y" → false
  if (t.isUnaryExpression(node, { operator: "!" })) {
    if (t.isArrayExpression(node.argument)) {
      return true;  // ![] → false
    }
    if (t.isObjectExpression(node.argument)) {
      return true;  // !{} → false
    }
    if (t.isNumericLiteral(node.argument) && node.argument.value !== 0) {
      return true;  // !1 → false, !2 → false ...
    }
  }
  return false;
}
```

---

## 十二、实战 6：控制流平坦化还原

### 12.1 混淆原理

控制流平坦化 (Control Flow Flattening) 把原本顺序执行的代码块打乱，用一个 `while + switch` 分发器控制执行顺序：

```javascript
// === 原始代码 ===
function encrypt(data) {
  var key = "secret";
  var result = md5(data + key);
  return result;
}

// === 混淆后（控制流平坦化）===
function encrypt(data) {
  var _0x = "3|0|1|2".split("|");  // 执行顺序
  var _0xi = 0;
  var key, result;

  while (true) {
    switch (_0x[_0xi++]) {         // 分发器: 按 _0x 数组顺序执行
      case "0":
        key = "secret";
        continue;
      case "1":
        result = md5(data + key);
        continue;
      case "2":
        return result;
      case "3":
        _0xi = 0;                  // 入口
        continue;
    }
    break;
  }
}
```

### 12.2 还原策略

```
步骤 1: 找到分发器变量 (_0x = "3|0|1|2".split("|"))
  ↓
步骤 2: 解析执行顺序 [3 → 0 → 1 → 2]
  ↓
步骤 3: 按顺序收集每个 case 的代码块
  ↓
步骤 4: 移除 switch 和 while 包装
  ↓
步骤 5: 重组为顺序代码
```

### 12.3 简化实现

```javascript
function flattenControlFlow(ast) {
  traverse(ast, {
    WhileStatement(path) {
      // 检测 while(true) + switch 模式
      if (!t.isBooleanLiteral(path.node.test, { value: true })) return;

      const body = path.node.body.body;
      if (body.length === 0) return;

      const switchStmt = body.find(
        s => t.isSwitchStatement(s)
      );
      if (!switchStmt) return;  // 不是控制流平坦化

      // 1. 找到分发器: switch (_0x[_0xi++])
      const discriminant = switchStmt.discriminant;
      if (!t.isMemberExpression(discriminant)) return;
      // ... (检查是否是数组索引访问模式)

      // 2. 提取 case 顺序
      const cases = switchStmt.cases;
      const caseMap = new Map();  // test → consequent

      for (const c of cases) {
        if (t.isStringLiteral(c.test)) {
          // 去除 continue 和 break
          const body = c.consequent.filter(
            s => !t.isContinueStatement(s) && !t.isBreakStatement(s)
          );
          caseMap.set(c.test.value, body);
        }
      }

      // 3. 找到执行顺序数组 (在变量声明中)
      // var _0x = "3|0|1|2".split("|")
      // 简化为: 手动指定或从父作用域找

      // 4. 按顺序拼接代码块
      const order = ["3", "0", "1", "2"];  // 需要动态提取
      const orderedBody = [];
      for (const key of order) {
        const block = caseMap.get(key);
        if (block) orderedBody.push(...block);
      }

      // 5. 替换 while 为顺序块
      path.replaceWithMultiple(orderedBody);
    }
  });
}
```

### 12.4 进阶：自动提取执行顺序

要从代码中自动提取执行顺序，需要找到分发器数组的初始化：

```javascript
// 提取 var _0x = "3|0|1|2".split("|") 中的顺序
function extractOrder(ast, varName) {
  let order = null;

  traverse(ast, {
    VariableDeclarator(path) {
      const node = path.node;
      if (
        t.isIdentifier(node.id, { name: varName }) &&
        t.isCallExpression(node.init) &&
        t.isMemberExpression(node.init.callee) &&
        t.isStringLiteral(node.init.callee.object)
      ) {
        // "3|0|1|2".split("|") → ["3","0","1","2"]
        order = node.init.callee.object.value.split("|");
      }
    }
  });

  return order;
}
```

---

## 十三、实战 7：自执行函数解密

### 13.1 混淆原理

有些混淆器把代码放在一个自执行函数里，通过立即执行解密：

```javascript
// === 混淆后 ===
(function() {
  var _0x = ["encrypt", "decrypt", "sign"];
  // ... 解密后定义真正的函数 ...
  window.realFunction = function() { /* ... */ };
})();

// 这层包装没有值的转换，只是为了隔离作用域
// 还原策略: 提取函数体，提升到顶层
```

更复杂的情况——自执行函数是一层"解密器"：

```javascript
// === 解密包装 ===
var _0xa1b2 = function(_0x3c4d) {
  // 复杂的解密算法 ...
  return decrypted;
}("base64EncodedString");

// _0xa1b2 解密后是一段新的 JS 代码字符串
// 需要 eval 或进一步解析
```

### 13.2 还原策略

```javascript
function unwrapIIFE(ast) {
  // 找到形如 (function(){...})() 或 !function(){...}()
  traverse(ast, {
    ExpressionStatement(path) {
      const expr = path.node.expression;

      // 模式: (function(){ ... })()
      if (
        t.isCallExpression(expr) &&
        t.isFunctionExpression(expr.callee) &&
        expr.callee.params.length === 0  // 无参数 → 无外部依赖
      ) {
        const body = expr.callee.body.body;

        // 检查 IIFE 内部是否有副作用（赋值给 window/exports/全局变量等）
        // 如果有，提升到顶层
        const hasExternalEffect = hasSideEffect(body);

        if (!hasExternalEffect) {
          // 纯计算 IIFE，可以安全移除
          if (body.every(s => t.isVariableDeclaration(s))) {
            // 全部是变量声明 → 提升到顶层
            path.replaceWithMultiple(body);
          }
        } else {
          // 有副作用的 IIFE，提取函数体但保留调用
          path.replaceWithMultiple(body);
        }
      }
    }
  });
}

function hasSideEffect(body) {
  // 检查是否有赋值给非局部变量、函数调用等
  return body.some(stmt => {
    if (t.isExpressionStatement(stmt)) {
      const expr = stmt.expression;
      // window.xxx = ... (有副作用)
      if (t.isAssignmentExpression(expr)) {
        if (
          t.isMemberExpression(expr.left) &&
          t.isIdentifier(expr.left.object, { name: "window" })
        ) {
          return true;
        }
      }
    }
    return false;
  });
}
```

### 13.3 更复杂的：eval 解密层

```javascript
// === 混淆代码 ===
eval(function(p, a, c, k, e, r) {
  // 这是著名的 Packer 混淆 (Dean Edwards)
  e = function(c) {
    return c.toString(36);  // 数字 → 36 进制
  };
  // ...
  return ...;
}('1 2="hello";3(2);', 4, 4, 'var|world|console|log'.split('|'), 0, {}));

// 还原策略:
// 1. 识别 eval(function(p,a,c,k,e,r){...}(...)) 模式
// 2. 提取参数 (p, a, c, k, e, r)
// 3. 用 Node.js 直接 eval 执行（沙箱安全）
// 4. 对解密结果重新解析为 AST
```

---

## 十四、高级技巧

### 14.1 多趟遍历 (Multi-Pass)

反混淆不是一次性完成的，需要多趟遍历：

```javascript
function deobfuscate(code) {
  let ast = parser.parse(code);

  // Pass 1: 展开 IIFE
  unwrapIIFE(ast);

  // Pass 2: 提取字符串数组
  const stringArrays = extractStringArrays(ast);

  // Pass 3: 还原字符串引用
  restoreStringReferences(ast, stringArrays);

  // Pass 4: 常量折叠（多次直到收敛）
  ast = constantFoldingFull(ast);

  // Pass 5: 移除死代码
  removeDeadCode(ast);

  // Pass 6: 简化表达式
  simplifyExpressions(ast);

  // 生成最终代码
  return generate(ast, { comments: false }).code;
}
```

### 14.2 作用域感知的变量重命名

利用 `path.scope` 进行安全的重命名：

```javascript
traverse(ast, {
  Identifier(path) {
    // 跳过属性名
    if (path.parentPath.isMemberExpression() && path.key === "property") return;
    // 跳过声明
    if (path.parentPath.isVariableDeclarator() && path.key === "id") return;
    // 跳过函数名
    if (path.parentPath.isFunctionDeclaration() && path.key === "id") return;

    const binding = path.scope.getBinding(path.node.name);
    if (!binding) return;  // 全局变量，跳过

    // 只重命名混淆的变量 (_0x 前缀)
    if (path.node.name.startsWith("_0x")) {
      // 根据用途生成有意义的名字
      if (binding.path.node.init && t.isStringLiteral(binding.path.node.init)) {
        path.node.name = "str_" + binding.path.node.init.value;
      }
    }
  }
});
```

### 14.3 批量替换模式

```javascript
// 预定义混淆模式映射
const PATTERNS = {
  // 混淆表达式 → 真实含义
  "!![]": "true",
  "![]": "false",
  "!!{}": "true",
  "!{}": "false",
  "void 0": "undefined",
  "undefined": "undefined",
};

// 对每种模式，构建对应的 AST 节点匹配和替换
function simplifyJunkExpressions(ast) {
  traverse(ast, {
    UnaryExpression(path) {
      // !![] → true
      if (
        path.node.operator === "!" &&
        t.isUnaryExpression(path.node.argument, { operator: "!" }) &&
        t.isArrayExpression(path.node.argument.argument, { elements: [] })
      ) {
        path.replaceWith(t.booleanLiteral(true));
      }
      // ![] → false
      else if (
        path.node.operator === "!" &&
        t.isArrayExpression(path.node.argument, { elements: [] })
      ) {
        path.replaceWith(t.booleanLiteral(false));
      }
    }
  });
}
```

### 14.4 使用 @babel/traverse 的 `noScope` 优化

```javascript
// 不需要作用域分析时，关闭 scope 可以显著提速
traverse(ast, {
  StringLiteral: {
    enter(path) { /* ... */ }
  },
  noScope: true  // ← 2-3 倍性能提升
});
```

### 14.5 保持注释和格式

```javascript
const output = generate(ast, {
  comments: true,     // 保留注释
  compact: false,     // 不压缩（保留缩进和换行）
  retainLines: true,  // 尽量保持行号
}).code;
```

---

## 十五、常见问题与调试

### 15.1 "Node has been removed" 错误

```javascript
// ❌ 错误: 同时遍历和修改导致问题
traverse(ast, {
  VariableDeclarator(path) {
    if (shouldRemove(path)) {
      path.remove();
      console.log(path.node.id.name);  // ❌ 节点已被删除！
    }
  }
});
```

**解决**：不要在 `remove()` 后访问 `path.node`。

### 15.2 "replaceWith multiple times" 错误

```javascript
// ❌ 错误: 对一个 path 多次调用 replaceWith
path.replaceWith(node1);
path.replaceWith(node2);  // ❌ 报错

// ✅ 正确: 只调用一次
path.replaceWith(node2);
```

### 15.3 替换后遍历到旧节点

```javascript
// Babel traverse 会自动跳过替换后的节点
// 但如果你在 enter 中替换，子节点遍历可能异常
// 建议在 exit 回调中做替换操作
traverse(ast, {
  BinaryExpression: {
    exit(path) {  // ← 使用 exit 而不是 enter
      if (canFold(path)) {
        path.replaceWith(t.numericLiteral(result));
      }
    }
  }
});
```

### 15.4 调试技巧

```javascript
// 1. 打印当前节点的上下文
path.toString();  // 打印节点对应的源代码

// 2. 检查父节点
console.log("parent:", path.parent.type);
console.log("parent code:", path.parentPath.toString());

// 3. 检查作用域
console.log("scope bindings:", Object.keys(path.scope.bindings));

// 4. 验证替换是否合法
if (path.replaceWith) {
  // 某些 path 类型没有 replaceWith 方法
}

// 5. 用 try-catch 包裹遍历
try {
  traverse(ast, { /* ... */ });
} catch (e) {
  console.error("遍历出错:", e.message);
  // 打印出错时的代码
  console.error("当前节点:", e.path?.toString());
}
```

### 15.5 常见混淆家族速查

| 家族 | 特征字符串 | 检测方法 |
|---|---|---|
| **obfuscator.io** | `_0x` + 十六进制 | `/_0x[0-9a-f]{4,}/` |
| **JSDefender** | `___closure_` | 闭包嵌套 |
| **JScrambler** | `JSCR` 标记 | 多层变换 |
| **sojson** | `jsjiami.com` | URL 检测 |
| **Akamai** | `bmak` 前缀 | CDN 脚本 |
| **瑞数** | `$d` 前缀 | CDN 脚本 |
| **顶象** | `dx__` | SDK 脚本 |
| **极验4** | `load` 回调 | 动态加载 |

---

## 十六、练习清单

按难度递增排列，建议按顺序完成：

### ⭐ 初级

- [ ] **练习 1**: 写一个脚本，统计某个 JS 文件中每种 AST 节点类型的数量
- [ ] **练习 2**: 把所有 `var` 替换成 `let`
- [ ] **练习 3**: 提取 `search_gxb.js` 中所有 `$.ajax()` 调用的 URL

### ⭐⭐ 中级

- [ ] **练习 4**: 还原一个 OB 混淆的简单脚本（从 obfuscator.io 生成）
- [ ] **练习 5**: 写一个脚本来把字符串常量 `"a"+"b"` 折叠成 `"ab"`
- [ ] **练习 6**: 移除所有 `debugger;` 语句

### ⭐⭐⭐ 中高级

- [ ] **练习 7**: 对一个有 2 层 eval 的 Packer 混淆进行解包
- [ ] **练习 8**: 还原 sojson 混淆的基本脚本
- [ ] **练习 9**: 写一个控制流平坦化的检测器（不一定要完全还原）

### ⭐⭐⭐⭐ 高级

- [ ] **练习 10**: 完整还原一个 obfuscator.io 高混淆配置的输出
- [ ] **练习 11**: 对 JSVMP 保护的代码提取操作码映射表
- [ ] **练习 12**: 写一个通用的 JS 反混淆框架，支持插件化扩展

---

## 附录 A: Babel AST 常用节点速查卡

```
┌──────────────────────────────────────────────────────────┐
│                    表达式 (Expression)                      │
├────────────────────┬─────────────────────────────────────┤
│ StringLiteral      │ "hello"   value: "hello"            │
│ NumericLiteral     │ 123       value: 123                │
│ BooleanLiteral     │ true      value: true               │
│ Identifier         │ myVar     name: "myVar"             │
│ BinaryExpression   │ a + b     left, operator, right     │
│ UnaryExpression    │ !a        operator, argument         │
│ CallExpression     │ foo()     callee, arguments[]        │
│ MemberExpression   │ obj.prop  object, property, computed│
│ ArrayExpression    │ [1,2]     elements[]                 │
│ ObjectExpression   │ {a:1}     properties[]               │
├────────────────────┴─────────────────────────────────────┤
│                    语句 (Statement)                        │
├────────────────────┬─────────────────────────────────────┤
│ ExpressionStatement│ foo();     expression                │
│ VariableDeclaration│ var x=1;   declarations[]            │
│ ReturnStatement    │ return x;  argument                  │
│ IfStatement        │ if(x){}    test, consequent, alternate│
│ ForStatement       │ for(;;){}  init, test, update, body  │
│ WhileStatement     │ while(x){} test, body                │
│ SwitchStatement    │ switch(x){} discriminant, cases[]    │
│ BlockStatement     │ {}         body[]                    │
├────────────────────┴─────────────────────────────────────┤
│                    声明 (Declaration)                      │
├────────────────────┬─────────────────────────────────────┤
│ FunctionDeclaration│ function f(){} id, params, body      │
│ VariableDeclarator │ x = 1       id, init                 │
└────────────────────┴─────────────────────────────────────┘
```

## 附录 B: 项目文件索引

| 文件 | 说明 |
|---|---|
| `ast_extract.js` | AST 函数提取 + 调用链分析（56个函数） |
| `ast_deobfuscate_demo.js` | 完整 OB 反混淆演示 |
| `search_gxb.js` | 原始 JS 文件（49KB，分析目标） |
| `encode64_tool.py` | JS→Python 的 encode64 实现 |
| `spider.py` | Python 搜索 API 客户端 |

---

> **下一步**: 选择一个有 OB 混淆的真实站点（如 obfuscator.io 保护的网站），应用本文的技术进行实战练习。
> 推荐从 [obfuscator.io](https://obfuscator.io/) 自己生成混淆代码开始练手。
