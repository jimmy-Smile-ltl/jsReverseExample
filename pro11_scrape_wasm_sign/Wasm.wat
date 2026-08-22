;; spa14.scrape.center - Wasm.wasm 反编译
;; 使用 wasm2wat 工具反编译
;; 命令: wasm2wat Wasm.wasm

(module
  (type (;0;) (func))
  (type (;1;) (func (param i32)))
  (type (;2;) (func (result i32)))
  (type (;3;) (func (param i32) (result i32)))
  (type (;4;) (func (param i32 i32) (result i32)))
  (func (;0;) (type 0)
    nop)
  (func (;1;) (type 3) (param i32) (result i32)
    global.get 0
    local.get 0
    i32.sub
    i32.const -16
    i32.and
    local.tee 0
    global.set 0
    local.get 0)
  (func (;2;) (type 1) (param i32)
    local.get 0
    global.set 0)
  (func (;3;) (type 2) (result i32)
    global.get 0)
  ;; ★★★ 核心函数 ★★★
  ;; sign = encrypt(offset, timestamp)
  ;; 即: return offset + timestamp / 3 + 16358
  (func (;4;) (type 4) (param i32 i32) (result i32)
    local.get 0       ;; push offset
    local.get 1       ;; push timestamp
    i32.const 3       ;; push 3
    i32.div_s         ;; timestamp / 3 (有符号整除)
    i32.add           ;; offset + timestamp / 3
    i32.const 16358   ;; push 16358
    i32.add)          ;; offset + timestamp / 3 + 16358
  (table (;0;) 2 2 funcref)
  (memory (;0;) 256 256)
  (global (;0;) (mut i32) (i32.const 5243920))
  (export "memory" (memory 0))
  (export "encrypt" (func 4))
  (export "__indirect_function_table" (table 0))
  (export "_initialize" (func 0))
  (export "stackSave" (func 3))
  (export "stackRestore" (func 2))
  (export "stackAlloc" (func 1))
  (elem (;0;) (i32.const 1) func 0))
