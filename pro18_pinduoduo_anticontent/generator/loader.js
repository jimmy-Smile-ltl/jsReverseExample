/**
 * 拼多多 anti_content - Webpack 模块加载器
 *
 * 加载顺序: webpack.js → main.js → commons.js → subject.js
 * 通过 patch webpack runtime 暴露 __webpack_require__ 函数。
 */

const fs = require('fs');
const path = require('path');
const vm = require('vm');

// ============================================================
// 配置
// ============================================================
// [本地化 patch] 原项目 bundles 位于补环境目录的上级 (analysis/),
// 复现仓库将 webpack.js/main.js/subject.js 与脚本同放 generator/ 下
const ANALYSIS_DIR = __dirname;
const BUNDLES = [
  { name: 'webpack.js', path: path.join(ANALYSIS_DIR, 'webpack.js') },
  { name: 'main.js',    path: path.join(ANALYSIS_DIR, 'main.js') },
  { name: 'subject.js', path: path.join(ANALYSIS_DIR, 'subject.js') },
];

// ============================================================
// 加载器
// ============================================================
class WebpackLoader {
  constructor() {
    this.requireFn = null;
    this.loaded = false;
    this.errors = [];
  }

  /**
   * 读取并 patch webpack runtime, 暴露 require 函数到全局
   */
  _patchRuntime(code) {
    // 原始 webpack runtime 末尾:
    //   var f=window.webpackJsonp=...,i=f.push.bind(f);f.push=r,f=f.slice();
    //   for(var a=0;a<f.length;a++)r(f[a]);var p=i;t()
    //
    // 在 t() 之前注入: global.__webpack_require__ = l;
    // 其中 l 是 require 函数, t 是入口执行函数

    // 在代码末尾的 t() 之前插入补丁
    // 匹配模式: ...};var p=i;t()
    const patched = code.replace(
      /var p=i;t\(\)/,
      'var p=i;global.__webpack_require__=l;t()'
    );

    if (patched === code) {
      console.warn('[loader] WARNING: webpack runtime patch 未匹配, 可能需要手动调整');

      // 尝试另一种模式
      const altPatched = code.replace(
        /t\(\)$/m,
        'global.__webpack_require__=l;t()'
      );
      if (altPatched !== code) {
        console.log('[loader] 使用备用 patch 模式');
        return altPatched;
      }
    }

    return patched;
  }

  /**
   * 加载所有 webpack bundles
   */
  load() {
    console.log('[loader] ===== 开始加载 webpack bundles =====');

    // 先加载 mock 模块（注入 regeneratorRuntime）
    // [本地化 patch] 原项目从上级 node_modules 解析 regenerator-runtime,
    // 复现仓库 vendored 同目录 regenerator-runtime.js (MIT)
    global.__regeneratorRuntime = require('./regenerator-runtime.js');
    const mocksCode = require('fs').readFileSync(require('path').join(__dirname, 'mocks.js'), 'utf-8');
    (0, eval)(mocksCode);
    console.log('[loader] mock modules injected');

    // 禁用 MessageChannel 让 React scheduler 走 setTimeout 回退
    try { delete global.MessageChannel; global.MessageChannel = undefined; } catch(e) {}

    console.log('[loader] MessageChannel check: ' + typeof global.MessageChannel);
    for (const bundle of BUNDLES) {
      if (!fs.existsSync(bundle.path)) {
        const err = `文件不存在: ${bundle.path}`;
        console.error(`[loader] ${err}`);
        this.errors.push(err);
        return false;
      }

      let code = fs.readFileSync(bundle.path, 'utf-8');
      console.log(`[loader] 读取 ${bundle.name}: ${code.length} bytes`);

      // 对 webpack.js 做 patch
      if (bundle.name === 'webpack.js') {
        code = this._patchRuntime(code);
        console.log(`[loader] webpack.js 已 patch (暴露 __webpack_require__)`);
      }

      // 执行代码
      try {
        // 使用 vm.runInThisContext 保持全局作用域一致
        (0, eval)(code);
        console.log(`[loader] ${bundle.name} 加载成功`);
      } catch (e) {
        console.error(`[loader] ${bundle.name} 加载失败:`, e.message);
        if (e.stack) {
          // 只显示前 10 行
          const lines = e.stack.split('\n').slice(0, 10);
          console.error(lines.join('\n'));
        }
        this.errors.push(`${bundle.name}: ${e.message}`);
        return false;
      }
    }

    // 检查是否获取到 require 函数
    if (typeof global.__webpack_require__ === 'function') {
      this.requireFn = global.__webpack_require__;
      this.loaded = true;
      console.log('[loader] ===== 加载完成! =====');
      console.log(`[loader] 模块总数: ${Object.keys(this.requireFn.m).length}`);

      // 检查关键模块
      for (const id of ['TPp2', 'fbeZ', 's6vS', 'o0o1', '8oxB', 'YuTi']) {
        const exists = id in this.requireFn.m;
        console.log(`[loader]   ${id}: ${exists ? '✓' : '✗ 未找到'}`);
      }
    } else {
      console.error('[loader] ===== 加载失败: 未获取到 __webpack_require__ =====');

      // 尝试其他方式
      if (global.window && global.window.__webpack_require__) {
        this.requireFn = global.window.__webpack_require__;
        this.loaded = true;
        console.log('[loader] 从 window.__webpack_require__ 获取成功');
      } else {
        this.errors.push('未获取到 __webpack_require__');
      }
    }

    return this.loaded;
  }

  /**
   * 获取 webpack require 函数
   */
  get require() {
    return this.requireFn;
  }

  /**
   * 获取模块定义表 (l.m)
   */
  get modules() {
    return this.requireFn ? this.requireFn.m : {};
  }

  /**
   * 获取模块缓存 (l.c)
   */
  get cache() {
    return this.requireFn ? this.requireFn.c : {};
  }

  /**
   * 列出所有模块 ID
   */
  listModules(filter) {
    const ids = Object.keys(this.modules);
    if (filter) return ids.filter(id => id.includes(filter) || id.match(filter));
    return ids;
  }
}

// ============================================================
// 导出
// ============================================================
module.exports = { WebpackLoader };
