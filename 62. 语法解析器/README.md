# 62. 语法解析器（Parser）

递归下降解析器，将算术 + 比较 + 布尔表达式解析为 AST，并以 S 表达式 + 树形输出。

## 用法
```
python parser.py "1 + 2 * 3"
python parser.py "a*(b+c) > 0 and not flag"
python parser.py "x ** 2 + y ** 2 == r ** 2"
```

## 文法
```
expr := or
or   := and ('or' and)*
and  := not ('and' not)*
not  := 'not' not | comp
comp := add (('<'|'>'|'<='|'>='|'=='|'!=') add)?
add  := mul (('+'|'-') mul)*
mul  := pow (('*'|'/'|'%') pow)*
pow  := unary ('**' pow)?
unary:= ('+'|'-') unary | atom
atom := NUMBER | IDENT ['(' args ')'] | '(' expr ')'
```
