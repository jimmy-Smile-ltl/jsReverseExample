# 爱企查 (aiqicha.baidu.com) 反调试与安全机制分析报告

> 分析日期: 2026-06-30
> 分析工具: CloakBrowser (stealth Chromium)

---

## 一、整体架构概览

爱企查使用百度自研的多层安全防护体系，由以下组件构成：

```
┌─────────────────────────────────────────────────────┐
│                    aiqicha.baidu.com                 │
├─────────────────────────────────────────────────────┤
│  第1层: ABCLite SDK (反调试/设备指纹)                  │
│    - abclite-2061-s.js (加载器，每20分钟刷新)          │
│    - abclite-2061-s.original.js (核心SDK, ~192KB)    │
├─────────────────────────────────────────────────────┤
│  第2层: ACS-2061 (反作弊/请求签名)                     │
│    - acs-2061.js (AES加密 + 数据采集)                 │
├─────────────────────────────────────────────────────┤
│  第3层: Trust Receiver (信任评估)                     │
│    - trustrcv.min.js                                │
├─────────────────────────────────────────────────────┤
│  第4层: 业务层安全                                     │
│    - 强制登录才能搜索                                   │
│    - 扫码登录 (APP扫码)                                │
│    - 第三方登录 (微博/微信/QQ)                           │
├─────────────────────────────────────────────────────┤
│  数据采集:                                            │
│    - hm.baidu.com (百度统计/风控)                     │
│    - miao.baidu.com (用户行为追踪)                     │
│    - sofire.bdstatic.com (反欺诈)                     │
└─────────────────────────────────────────────────────┘
```

---

## 二、ABCLite SDK 反调试机制（第1层）

**核心文件**: `https://dlswbr.baidu.com/heicha/mw/abclite-2061-s.js`

### 2.1 加载机制

```javascript
// 动态加载原始SDK，URL含时间戳缓存破坏
var e = 2061;  // SDK版本号
var u = +new Date;
var c = "?_=" + parseInt(u/1728e5, 10);  // 每20分钟(172800000ms)刷新一次
var l = "https://dlswbr.baidu.com/heicha/mw/abclite-" + e + "-s.original.js" + c;

// 创建全局对象 window.BCat_2061
window.BCat_2061 = {
    initData,       // 初始化数据采集
    initActiveData, // 初始化活跃数据
    report,         // 上报
    init,           // 初始化
    dr5,            // DR5接口
    miao,           // 喵追踪
    miaowu          // 喵呜追踪
};
```

### 2.2 DevTools 检测 (核心)

ABCLite 通过劫持 `window.eval` 来检测开发者工具:

```javascript
// 1. 使用 Object.defineProperty 劫持 eval
var gF = '__eval_hook_flag__';
var gG = window['eval'][gF] || function(ab) { return eventBus.emit(0, ab); };

(function() {
    var ab = window['eval'];
    var ad = window['Object'];
    if (ab[gF] || !ad['defineProperty']) return false;
    
    ab[gF] = gG;
    // 关键: 劫持 window.eval 的 getter
    ad.defineProperty(window, 'eval', {
        'get': function() {
            var stack = new Error().stack;  // 获取调用栈
            if (stack) {
                eventBus.emit(0, stack);     // 发送给检测模块
            }
            return ab;  // 返回真正的 eval
        }
    });
})();
```

**检测原理**:
- 当 DevTools 打开时，Chrome 会在 `eval()` 执行的堆栈中添加 `evaluate@debugger` 标记
- 通过分析 `Error().stack` 中的 `@debugger` 行来判断 DevTools 是否开启

```javascript
// DevTools 检测函数
function detectDevtools(stack) {
    var lines = stack.split('\n');
    for (var i = 0; i < lines.length - 1; i++) {
        // 检测 evaluate@debugger 模式
        if (lines[i].indexOf('evaluate@debugger') > -1 &&
            lines[i+1] && lines[i+1].indexOf('@debugger') === 0) {
            return !lines[i+2]; // 返回检测结果
        }
    }
    return true; // 正常浏览器环境
}
```

### 2.3 自动化工具检测 (WebDriver/Selenium)

检测以下自动化框架注入的全局变量:

```javascript
// 检测的 WebDriver 标记 (解码后)
var driverFlags = [
    '__driver_evaluate',          // Selenium WebDriver
    '__fxdriver_evaluate',        // Firefox WebDriver
    '__webdriver_script_func',    // WebDriver 脚本函数
    '__fxdriver_unwrapped',       // Firefox 未包装
    '__$webdriverAsyncExecutor',  // WebDriver 异步执行器
    '__nightmare'                 // Nightmare.js
];

// 通过 Object.getOwnPropertyNames 遍历 window 检测
function checkWebDriver() {
    var results = [];
    Object.getOwnPropertyNames(window).forEach(function(key) {
        if (driverFlags.indexOf(key) > -1) {
            results.push(flagCode);
        }
    });
    return results.join('_');
}
```

### 2.4 窗口尺寸检测

```javascript
function checkWindowDimensions() {
    var flags = [];
    var targetW = 800, targetH = 600, targetOW = 1200;  // 标准桌面尺寸
    
    // 检测特定尺寸 (可能是无头浏览器默认值)
    if (window.innerWidth === targetW && 
        window.innerHeight === targetH && 
        window.outerWidth === targetOW) {
        flags.push(0x1388);  // 命中: 5000
    }
    
    // 关键: outerWidth === 0 是无头浏览器特征
    if (window.outerWidth === 0) {
        flags.push(0x1389);  // 命中: 5001
    }
    
    return flags.join('_');
}
```

### 2.5 浏览器特征检测

```javascript
function checkBrowserFeatures() {
    var flags = [];
    
    // 1. chrome.runtime 检测
    if (window.chrome && window.chrome.runtime) {
        flags.push(0x1bbc);  // 浏览器扩展/自动化特征
    }
    
    // 2. navigator 属性链检测
    if (typeof navigator.webdriver === 'string' && 
        typeof navigator.selenium === 'string') {
        flags.push(0x1c20);
    }
    
    // 3. 插件/MIME类型完整性检测
    // 通过 iframe 沙箱对比 navigator.plugins
    
    // 4. WebGL 指纹
    if (window.WebGLRenderingContext) {
        flags.push(0x258);  // 600
    }
    if (window.WebGL2RenderingContext) {
        flags.push(0x259);  // 601
    }
    
    return flags.join('_');
}
```

### 2.6 Function.prototype.toString 检测

```javascript
function detectToStringTampering() {
    var flags = [];
    
    try {
        // 调用原生 toString 看是否被篡改
        window['Function']['prototype']['toString']['call']('');
        return false;  // 正常情况不会抛异常
    } catch(e) {
        if (e.stack) {
            // 分析异常堆栈行数 (DevTools打开时堆栈更长)
            var stackLines = e.stack.split('\n').length;
            var normalLines = new Error().stack.split('\n').length;
            
            if (stackLines < normalLines) {
                flags.push(0x64);  // 100 - toString被篡改
            }
        }
    }
    
    return flags.join('_');
}
```

### 2.7 Canvas 指纹采集

```javascript
function Y6() {
    // 检测 Canvas 2D 支持
    var canvas = document.createElement('canvas');
    try {
        return !!(!canvas.getContext || !canvas.getContext('2d')) + 0;
    } catch(e) {
        return 0;
    }
}

function Y9() {
    // WebGL 指纹采集
    // 获取 UNMASKED_VENDOR_WEBGL / UNMASKED_RENDERER_WEBGL
    // 用于 GPU 指纹识别
}
```

### 2.8 Battery API 检测

```javascript
function collectBattery(ab) {
    var ad, af;
    var BatteryManager = navigator.getBattery || navigator.battery || navigator.webkitBattery;
    
    // 超时回退
    setTimeout(function() {
        ab([-1, -1, -1, -1]);  // 不支持或无头默认
    }, 110);
    
    // 获取电池信息
    navigator.getBattery().then(function(battery) {
        ab([
            battery.level,           // 电量
            battery.chargingTime,    // 充电时间
            battery.dischargingTime, // 放电时间
            battery.charging         // 是否充电中
        ]);
    });
}
```

### 2.9 iframe 沙箱检测

通过创建隐藏 iframe 对比主窗口和 iframe 的属性差异来检测环境篡改:

```javascript
function iframeSandboxDetection(ab) {
    var iframe = document.createElement('iframe');
    iframe.style.display = 'none';
    iframe.style.width = '0';
    iframe.style.height = '0';
    document.body.appendChild(iframe);
    
    var iframeWindow = iframe.contentWindow;
    
    // 对比检测项:
    var checks = [
        function() { return iframeWindow.navigator !== window.navigator; },
        function() { return (iframeWindow.navigator.plugins || []).join(',') 
                          !== (window.navigator.plugins || []).join(','); },
        // ... 更多对比检查
    ];
}
```

---

## 三、ACS-2061 反作弊系统（第2层）

**核心文件**: `https://dlswbr.baidu.com/heicha/mm/2061/acs-2061.js`

### 3.1 技术栈

| 组件 | 实现 |
|------|------|
| 字符串加密 | 自定义 hex 编码 + Unicode 混淆 |
| 对称加密 | AES-128/256 (自实现，含完整密钥扩展) |
| 哈希 | HMAC-SHA256 |
| 编码 | 自定义 Base64 (标准字符集) |
| 数据序列化 | JSON → AES 加密 → Base64 编码 |

### 3.2 数据采集结构

```javascript
var FIELD_MAP = {
    'h0': 'h0',           // 设备指纹hash
    'h1': 'h1',           
    'hf': 'hf',           // 指纹特征
    'hfe': 'hfe',         // 指纹扩展
    'ua': 'ua',           // User-Agent
    'baiduid': 'baiduid', // 百度用户ID (从Cookie获取)
    'url': 'url',         // 当前页面URL
    'clientTs': 'clientTs', // 客户端时间戳
    'platform': 'platform', // 平台 (Win32/MacIntel等)
    'version': 'version',   // SDK版本
    'extraTooLong': 'extraTooLong', // 额外数据过长标记
    'extra': 'extra'       // 额外数据
};
```

### 3.3 签名生成流程

```javascript
// window.$BSB_2061.gs() — 生成安全签名
function generateSignature(extraData, callback) {
    // 1. 创建数据采集实例
    var collector = new FieldCollector();
    
    // 2. 收集浏览器指纹
    collector.set('baiduid', getCookie('BAIDUID'));
    collector.set('url', document.URL || location.href);
    collector.set('platform', navigator.platform);
    collector.set('ua', navigator.userAgent);
    collector.set('clientTs', Date.now());
    collector.set('version', '1.2.0');
    
    // 3. 附加业务数据
    if (extraData) {
        if (extraData.length > 1024) {
            collector.set('extraTooLong', 1);
            extraData = '';
        }
        collector.set('extra', extraData);
    }
    
    // 4. 采集完成后加密
    collector.getAllFields(function(fields) {
        var jsonData = JSON.stringify(fields);
        // 5. AES加密 + Base64编码
        var encrypted = aesEncrypt(jsonData, KEY_A0, IV_A1);
        var signature = Date.now() + '_' + encrypted;
        callback(signature);
    });
}
```

### 3.4 AES 加密实现

完整自实现 AES，包含:
- S-box 预计算表 (256项)
- 逆 S-box
- Galois Field 乘法表 (`0x11b` 不可约多项式)
- 密钥扩展 (支持 128/192/256 位)
- 加密轮函数 (SubBytes → ShiftRows → MixColumns → AddRoundKey)
- 解密轮函数
- PKCS7 填充

### 3.5 Base64 编码

使用标准 Base64 字符集:
```
ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/
```

### 3.6 密钥

```javascript
// ACS-2061 使用的加密密钥 (从混淆代码中)
var a0 = '...'  // AES 密钥 (混淆在代码中)
var a1 = '...'  // AES IV (混淆在代码中)
```

需要从混淆代码中提取。关键调用:
```javascript
window['$BSB_2061'] = {
    'gs': function(extraData, callback) {
        generateSignature(extraData, callback);
    }
};
```

---

## 四、业务层安全（第3-4层）

### 4.1 强制登录

搜索功能需要登录，未登录用户被重定向到:
```
https://aiqicha.baidu.com/login?u=<encoded_search_url>
```

### 4.2 登录方式

1. **APP扫码登录** (主推): 使用爱企查 APP 扫描二维码
2. **第三方登录**:
   - 新浪微博 OAuth
   - 微信 OAuth
   - QQ OAuth

### 4.3 搜索页面

搜索 URL 格式:
```
https://aiqicha.baidu.com/s?q=<keyword>&t=0
```

### 4.4 其他安全组件

| 组件 | URL | 作用 |
|------|-----|------|
| Trust Receiver | `xinpub.bj.bcebos.com/static/trustrcv.min.js` | 信任评分接收器 |
| 百度统计 | `hm.baidu.com/hm.js` | 用户行为分析 + 风控信号 |
| 喵追踪 | `miao.baidu.com/e.js` | 用户行为轨迹追踪 |
| 反欺诈 | `sofire.bdstatic.com/js/xaf.js` | 反欺诈检测 (CORS限制) |
| 百度通行证 | `passport.baidu.com/passApi/js/uni_login_wrapper.js` | 统一登录 |

---

## 五、反调试机制总结

### 5.1 检测技术矩阵

| 检测维度 | 技术手段 | 风险等级 |
|---------|---------|---------|
| DevTools检测 | eval() 劫持 + Error.stack 分析 | 🔴 高 |
| 自动化工具 | __driver_*/__nightmare 等全局变量检测 | 🔴 高 |
| 无头浏览器 | outerWidth=0 / 固定分辨率检测 | 🟡 中 |
| 环境篡改 | iframe 沙箱对比 / toString 检测 | 🟡 中 |
| 设备指纹 | Canvas/WebGL/Audio/Battery | 🟡 中 |
| 请求签名 | AES + HMAC + 动态时间戳 | 🔴 高 |
| 用户行为 | 鼠标轨迹/点击/滚动 (miao追踪) | 🟢 低 |
| 登录墙 | 强制登录才能搜索 | 🔴 高 |

### 5.2 绕过难度评估

| 措施 | 绕过难度 | 说明 |
|------|---------|------|
| eval 劫持检测 | ⭐⭐⭐ | 需要 patch eval getter |
| WebDriver 检测 | ⭐⭐ | CDP 直接连接可绕过 |
| 窗口尺寸 | ⭐ | 设置合理分辨率即可 |
| Canvas 指纹 | ⭐⭐⭐ | 需要虚拟化 Canvas |
| ACS 签名 | ⭐⭐⭐⭐ | 需提取 AES 密钥，或调用原函数 |
| 登录墙 | ⭐⭐⭐⭐⭐ | 需要有效账号 + Cookie管理 |

### 5.3 关键绕过点

1. **ABCLite**: Hook `window.BCat_2061` 的方法，返回虚假数据
2. **ACS**: 调用 `window.$BSB_2061.gs()` 获取合法签名
3. **eval 检测**: 在页面加载前 patch `Object.defineProperty`
4. **登录**: 使用有效 Cookie 维持会话

---

## 六、文件清单

| 文件 | 大小 | 说明 |
|------|------|------|
| `scripts/abclite_loader.js` | 1.3KB | ABCLite 加载器（格式化） |
| `abclite_original_formatted.js` | 192KB | ABCLite 核心SDK（JSON提取） |
| `abclite_decoded.js` | 162KB | hex解码后的核心SDK |
| `acs-2061.js` | ~60KB | ACS反作弊系统 |
| `decode_script.py` | - | hex解码工具 |
| `analyze_patterns.py` | - | 模式分析工具 |
| `deep_analyze.py` | - | 深度分析工具 |

---

## 七、后续研究方向

1. **提取 ACS AES 密钥**: 从混淆代码中提取 `a0`/`a1` 密钥
2. **分析 trustrcv.min.js**: 理解信任评分机制
3. **验证码分析**: 登录流程中的验证码处理
4. **Cookie 刷新策略**: BAIDUID 等关键Cookie的过期和刷新
5. **Python 爬虫实现**: 基于登录态 + ACS签名的完整爬虫
