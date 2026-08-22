// Mock webpack modules for Node.js env patching
// Uses real regenerator-runtime from shared node_modules
(function() {
  var regeneratorRuntime = global.__regeneratorRuntime;

  var wpj = global.window.webpackJsonp;
  wpj.push([
    ["__env_mocks__"],
    {
      "o0o1": function(m, e, r) {
        // Use real regeneratorRuntime - copy all its exports
        Object.assign(e, regeneratorRuntime);
        // Ensure mark and wrap are available
        if (!e.mark) e.mark = regeneratorRuntime.mark;
        if (!e.wrap) e.wrap = regeneratorRuntime.wrap;
      },
      "s6vS": function(m, e, r) {
        e.a = function(url, method, data, baseURL) {
          return Promise.resolve({ server_time: Math.floor(Date.now() / 1000) });
        };
        e.b = {
          defaults: { headers: {}, baseURL: "" },
          interceptors: { request: { use: function() {} }, response: { use: function() {} } },
          create: function() { return this; },
        };
      },
      "vDqi": function(m, e, r) {
        var axios = {
          create: function() { return axios; },
          defaults: { headers: {} },
          interceptors: { request: { use: function() {} }, response: { use: function() {} } },
          get: function() { return Promise.resolve({ data: { server_time: Math.floor(Date.now() / 1000) } }); },
          post: function() { return Promise.resolve({ data: {} }); },
        };
        Object.assign(e, axios);
        e.default = axios;
        e.__esModule = true;
      },
      "8oxB": function(m, e, r) {
        e.setTimeout = setTimeout;
        e.clearTimeout = clearTimeout;
      },
    },
    [["o0o1"], ["s6vS"], ["vDqi"], ["8oxB"]]
  ]);
})();
