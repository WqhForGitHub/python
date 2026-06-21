# 59. 简单解释器（表达式解析）

递归下降解析器实现的算术表达式求值。

## 支持
- `+ - * / % **`、一元正负、括号
- 变量赋值与引用：`x = 1+2`
- 内置函数：sin/cos/tan/sqrt/abs/min/max/log/exp/pow
- 内置常量：pi、e
- 上一次结果保存为 `_`

## 用法
```
python interpreter.py             # 进入 REPL
python interpreter.py "1+2*3"     # 直接求值
```

## 文法
```
statement := IDENT '=' expr | expr
expr      := term (('+'|'-') term)*
term      := factor (('*'|'/'|'%') factor)*
factor    := unary ('**' factor)?
unary     := ('+'|'-') unary | atom
atom      := NUMBER | IDENT ['(' args ')'] | '(' expr ')'
```
