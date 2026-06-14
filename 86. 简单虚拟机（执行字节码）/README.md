# PyVM —— 纯 Python 实现的栈式虚拟机（执行字节码）

完整演示一台经典栈式虚拟机的全链路：

```
源码 (mini lang) ──Lexer──▶ AST ──Compiler──▶ 字节码 ──VM──▶ 结果
```

## 用法

```bash
python pyvm.py demo                  # 编译 + 反汇编 + 执行内置示例
python pyvm.py asm script.pv         # 仅反汇编
python pyvm.py run script.pv         # 编译并执行
python pyvm.py save script.pv out.json   # 把字节码保存为 JSON
python pyvm.py vm out.json           # 直接加载字节码 JSON 并执行
```

## 源语言示例

```javascript
fn fact(n) {
    if (n <= 1) { return 1; }
    return n * fact(n - 1);
}
print("10! =", fact(10));

let xs = [1, 2, 3, 4, 5];
let s = 0;
for (let i = 0; i < len(xs); i = i + 1) {
    s = s + xs[i];
}
print(s);
```

## 指令集（栈式）

| 类别 | 指令 |
| --- | --- |
| 常量/变量 | `LOAD_CONST` `LOAD_NAME` `STORE_NAME` `LOAD_LOCAL` `STORE_LOCAL` |
| 栈操作 | `POP` `DUP` |
| 算术 | `BIN_ADD/SUB/MUL/DIV/MOD` `UNARY_NEG` |
| 比较 | `CMP_EQ/NE/LT/LE/GT/GE` |
| 逻辑 | `UNARY_NOT`（`&&`/`||` 由编译器用 `DUP+JUMP_IF_*` 短路实现） |
| 控制流 | `JUMP` `JUMP_IF_FALSE` `JUMP_IF_TRUE` |
| 函数 | `BUILD_FUNC` `CALL` `RETURN` |
| 容器 | `MAKE_LIST` `INDEX_GET` `INDEX_SET` |
| 其他 | `PRINT` `HALT` |

## 运行时模型

- **值栈** `stack`：所有计算结果都在这上面
- **调用栈** `frames`：每帧含 `(code, pc, locals[])`
- **常量池** 和 **名称池** 是 per-CodeObject 的
- 函数对象是一等公民：`BUILD_FUNC` 把 `CodeObject` 包成 `Function`，`CALL n` 创建新帧

## 反汇编输出（截选）

```
===== code <fact> nparams=1 nlocals=1 =====
   0  LOAD_LOCAL     0   ; n
   1  LOAD_CONST     0   ; 1
   2  CMP_LE
   3  JUMP_IF_FALSE  6
   4  LOAD_CONST     0   ; 1
   5  RETURN
   6  LOAD_LOCAL     0   ; n
   7  LOAD_LOCAL     0   ; n
   8  LOAD_CONST     1   ; 1
   9  BIN_SUB
  10  LOAD_NAME      0   ; fact
  11  CALL           1
  12  BIN_MUL
  13  RETURN
```

## 设计要点

1. **编译器**：单遍生成线性字节码；跳转目标用「先发占位 → patch 回填」。
2. **作用域**：顶层用 `LOAD_NAME / STORE_NAME` 走 `globals`；函数体用 `LOAD_LOCAL / STORE_LOCAL`，参数也是局部。
3. **短路求值**：`a && b` 编译为 `[a, DUP, JUMP_IF_FALSE end, POP, b, end:]`，无需新指令。
4. **可序列化**：`CodeObject.to_json()` / `from_json()` 让你把字节码持久化，独立于编译器加载执行。
5. **调试**：传 `VM(debug=True)` 可逐指令打印 `[pc] op arg stack`。

## 已知限制

- 无垃圾回收（依赖 Python GC）
- 函数无真正闭包（仅顶层全局名 + 局部变量；不捕获中间作用域）
- 没有异常 / 字符串切片 / 浮点格式化等高级特性
