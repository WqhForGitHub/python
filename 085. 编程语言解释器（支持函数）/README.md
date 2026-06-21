# PyLang —— 纯 Python 实现的小型编程语言解释器（支持函数）

经典「Lexer → Parser → Tree-Walking Interpreter」三段式实现，仅依赖 Python 标准库。

## 语言特性

| 特性 | 示例 |
| --- | --- |
| 数据类型 | `number / string / bool / nil / list / function` |
| 变量 | `let x = 1;` |
| 函数声明 | `fn add(a, b) { return a + b; }` |
| 匿名函数（lambda） | `fn(x) { return x * 2; }` |
| 一等函数、闭包 | `fn make_adder(x) { return fn(y) { return x+y; }; }` |
| 控制流 | `if / else / while / for / break / continue` |
| 算术 | `+ - * / %` |
| 比较 | `== != < <= > >=` |
| 逻辑 | `&& || !`（短路求值） |
| 列表 | `[1, 2, 3]`，`a[i]`，`a[i] = v` |
| 注释 | `// ...` |

## 内置函数

`print, len, push, pop, str, num, type, time`

## 用法

```bash
python pylang.py demo                 # 一键运行内置示例
python pylang.py run script.pl        # 运行脚本
python pylang.py repl                 # 交互式 REPL
```

## 示例脚本

```javascript
fn fact(n) {
    if (n <= 1) { return 1; }
    return n * fact(n - 1);
}
print(fact(10));               // 3628800

fn make_adder(x) {
    return fn(y) { return x + y; };
}
let add10 = make_adder(10);
print(add10(5));               // 15

fn map(arr, f) {
    let out = [];
    for (let i = 0; i < len(arr); i = i + 1) {
        push(out, f(arr[i]));
    }
    return out;
}
print(map([1,2,3], fn(v) { return v * v; }));   // [1, 4, 9]
```

## 设计要点

1. **Lexer**：手写状态机，识别数字、字符串（含 `\n \t \" \\` 转义）、标识符、关键字、单/双字符操作符。
2. **Parser**：递归下降 + 优先级爬升（`parse_binop(min_prec)`）。后缀解析 `f(x)` 与 `a[i]` 让函数调用 / 索引可链式。
3. **AST**：用 `dataclass` 写每个节点，简洁可视。
4. **Interpreter**：树形遍历 + 环境链。
   - `Env` 链式作用域，`define / get / set` 三 API
   - `Function` 捕获声明时的 `closure` 环境 → 闭包就地工作
   - 控制流通过 Python 异常 `_ReturnSignal / _BreakSignal / _ContinueSignal` 实现
5. **闭包**：`make_adder / counter` 例子直接可用，因为 `Function.closure` 持有的就是父环境的引用。

## 已知限制

- 不支持模块、类、字典、字符串切片
- 没有错误的源位置回溯（只到 token 行号）
- 解释器没做尾调用优化，深递归会撞 Python 栈
