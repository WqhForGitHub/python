# 简单解释器（表达式解析）

> 注：根据用户指示，本 demo 放置在「73. 简单 CI」目录下。

纯 Python 实现的迷你解释器，包含词法分析、递归下降语法分析、AST 求值。

## 支持
- 算术：`+ - * / % **`（幂右结合）
- 比较：`== != < <= > >=`
- 逻辑：`and / or / not`（短路）
- 一元：`-x`、`not x`
- 数据：整数、浮点、字符串（`'a'`/`"a"`）、`true / false / null`
- 变量：`x = 1; y = x + 2`
- 函数：`abs / max / min / len / sqrt / sin / cos / log / round / print` 等

## 用法
```bash
python interp.py                      # REPL
python interp.py "1+2*3"
python interp.py "x = sqrt(16); x*2"
```
