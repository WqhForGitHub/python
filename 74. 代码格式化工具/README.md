# μLang — 自定义编程语言（极简）

> 注：根据用户指示，本 demo 放置在「74. 代码格式化工具」目录下。

纯 Python 实现的极简编程语言：词法 + 递归下降解析 + 树遍历解释器。

## 语法概览
```
let x = 1
fn add(a, b) { return a + b }
if x < 10 { print("small") } else { print("big") }
while x < 5 { x = x + 1 }
for i in 0..len(xs) { print(xs[i]) }
let xs = [1, 2, 3]
```

## 特性
- 变量 `let` / 赋值
- 控制流：`if / else / while / for ... in lo..hi`
- 函数 `fn` + `return`，支持闭包
- 列表 `[1, 2, 3]`、索引访问
- 字符串、数字、布尔、null
- 内建：`print / len / push / pop / range / abs / min / max / int / float / str / bool / input`
- 注释：`#` 或 `//`

## 用法
```bash
python mulang.py example.ml     # 执行脚本
python mulang.py                # REPL
```
