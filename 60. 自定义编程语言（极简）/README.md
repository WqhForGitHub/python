# 60. 自定义编程语言（极简）—— MiniLang

完整的小型解释型语言：lexer + parser + tree-walking interpreter。

## 语法
```
let x = 1
fn add(a, b) { return a + b }
if x > 0 { print("pos") } else { print("non-pos") }
while x < 10 { x = x + 1 }
```

## 支持
- 数字 / 字符串 / 布尔 / null
- 算术 + 比较 + 逻辑 (&&, ||, !)
- if/else、while、函数、return、闭包
- print 内置

## 运行
```
python minilang.py examples/fib.ml
```
