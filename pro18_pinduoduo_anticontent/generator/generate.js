/**
 * 拼多多 anti_content 生成器 - 补环境方案
 *
 * 在 Node.js 中模拟浏览器环境，加载拼多多原始 webpack 代码，
 * 直接调用 TPp2 模块生成 anti_content。
 *
 * 用法:
 *   node generate.js [options]
 *
 * 选项:
 *   --tf-id=<id>    商品分类 ID (默认: TFRQ0v00000Y_13396)
 *   --json          以 JSON 格式输出
 *   --debug         显示调试信息
 *
 * 示例:
 *   node generate.js
 *   node generate.js --tf-id=TFRQ0v00000Y_13396 --json
 */

'use strict';

// ============================================================
// 1. 加载环境补丁
// ============================================================
console.log('[generate] ===== 拼多多 anti_content 补环境方案 =====');
console.log('[generate] 时间:', new Date().toISOString());

console.log('\n[generate] Step 1: 加载浏览器环境补丁...');
require('./env.js');

// ============================================================
// 2. 加载 webpack bundles
// ============================================================
console.log('\n[generate] Step 2: 加载 webpack bundles...');
const { WebpackLoader } = require('./loader.js');
const loader = new WebpackLoader();

if (!loader.load()) {
  console.error('[generate] 加载失败!');
  console.error('[generate] 错误:', loader.errors);
  process.exit(1);
}

const req = loader.require;
if (!req) {
  console.error('[generate] require 函数不可用');
  process.exit(1);
}

// ============================================================
// 3. 检查关键模块
// ============================================================
console.log('\n[generate] Step 3: 检查关键模块...');
const requiredModules = ['TPp2', 'fbeZ', 's6vS'];

let allReady = true;
for (const modId of requiredModules) {
  try {
    const mod = req(modId);
    console.log(`[generate]   ${modId}: ✓ (导出: ${Object.keys(mod || {}).join(', ') || 'none'})`);
  } catch (e) {
    console.error(`[generate]   ${modId}: ✗ ${e.message}`);
    allReady = false;
  }
}

if (!allReady) {
  console.error('[generate] 缺少关键模块, 无法继续');
  process.exit(1);
}

// ============================================================
// 4. 生成 anti_content
// ============================================================
async function generate() {
  console.log('\n[generate] Step 4: 初始化 fbeZ (获取 server_time)...');

  const tpp2 = req('TPp2');

  try {
    // 4a. 初始化: tpp2.b() → GET /api/server/_stm → new fbeZ({serverTime})
    console.log('[generate] 调用 tpp2.b()...');
    await tpp2.b();
    console.log('[generate] 初始化完成');
  } catch (e) {
    console.error('[generate] 初始化失败:', e.message);
    console.error('[generate] Stack:', e.stack?.substring(0, 500));

    // 尝试分析原因
    console.log('\n[debug] 初始化失败分析:');
    console.log('  - 可能是 /api/server/_stm 请求失败 (网络问题)');
    console.log('  - 可能是 fbeZ 模块依赖的浏览器 API 缺失');
    console.log('  - 可能是 8oxB 等依赖模块缺失');

    // 检查 fbeZ 模块
    try {
      const fbez = req('fbeZ');
      console.log(`  - fbeZ 类型: ${typeof fbez}`);
      if (typeof fbez === 'function') {
        console.log(`  - fbeZ 构造函数: ${fbez.name || 'anonymous'}`);
        console.log(`  - fbeZ 原型方法: ${Object.getOwnPropertyNames(fbez.prototype || {}).join(', ')}`);
      }
    } catch (e2) {
      console.log(`  - fbeZ 加载失败: ${e2.message}`);
    }

    process.exit(1);
  }

  // 4b. 生成 anti_content: tpp2.a() → fbeZ.messagePackSync()
  console.log('\n[generate] Step 5: 生成 anti_content...');

  try {
    const antiContent = await tpp2.a();

    console.log(`\n[generate] ===== 成功! =====`);
    console.log(`[generate] length: ${antiContent.length} chars`);
    console.log(`[generate] anti_content:`);
    console.log(antiContent);

    // 输出 JSON 格式 (方便 Python 解析)
    if (process.argv.includes('--json')) {
      console.log('\n[JSON]');
      console.log(JSON.stringify({
        success: true,
        anti_content: antiContent,
        length: antiContent.length,
        timestamp: Date.now(),
      }));
    }

    return antiContent;
  } catch (e) {
    console.error('[generate] 生成 anti_content 失败:', e.message);
    console.error('[generate] Stack:', e.stack?.substring(0, 500));
    process.exit(1);
  }
}

// ============================================================
// 5. 执行
// ============================================================
generate().catch(err => {
  console.error('[generate] 未捕获错误:', err);
  process.exit(1);
});
