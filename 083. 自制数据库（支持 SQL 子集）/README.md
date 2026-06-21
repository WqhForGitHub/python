# PyDB —— Python 实现的、支持 SQL 子集的迷你关系数据库

仅依赖 Python 标准库，单文件实现「Lexer → Parser → Executor → Storage」五层经典数据库架构。

## 支持的 SQL 子集

| 类别 | 语法 |
| --- | --- |
| DDL | `CREATE TABLE name (col TYPE [PRIMARY KEY] [NOT NULL], ...)` `DROP TABLE name` `SHOW TABLES` `DESCRIBE name` |
| DML | `INSERT INTO name [(c,...)] VALUES (...), ...`<br>`UPDATE name SET c=expr [, ...] [WHERE cond]`<br>`DELETE FROM name [WHERE cond]` |
| DQL | `SELECT [DISTINCT] expr [AS alias] [, ...] FROM name [WHERE cond] [ORDER BY col [ASC|DESC]] [LIMIT n]` |
| 事务 | `BEGIN` / `COMMIT` / `ROLLBACK`（基于内存快照） |
| 聚合 | `COUNT / SUM / AVG / MIN / MAX` |
| WHERE 操作符 | `= != <> < <= > >=` `AND OR NOT` `LIKE`（`%` `_`）`IN(...)` |
| 类型 | `INT / FLOAT / TEXT / BOOL` |
| 内置标量函数 | `UPPER / LOWER / LENGTH` |

## 用法

```bash
python pydb.py demo                  # 一键自测
python pydb.py shell mydata.json     # 交互式 SQL Shell
```

```sql
pydb> CREATE TABLE users (id INT PRIMARY KEY, name TEXT NOT NULL, age INT);
pydb> INSERT INTO users VALUES (1, 'alice', 30), (2, 'bob', 25);
pydb> SELECT name FROM users WHERE age > 26 ORDER BY age DESC;
pydb> SELECT COUNT(*), AVG(age) FROM users;
pydb> BEGIN;
pydb> UPDATE users SET age = 99 WHERE id = 1;
pydb> ROLLBACK;
```

## 设计

1. **Lexer**：单条正则按命名分支生成 token；支持 `'...'` 单引号字符串、数字、关键字、标识符。
2. **Parser**：递归下降，按 `OR > AND > NOT > 比较 > 主项` 的优先级建表达式 AST。
3. **Executor**：每个 SQL 节点对应一个 `do_*` 方法；表达式在「行字典」上求值。
4. **Storage**：JSON 文件持久化；事务通过 `deepcopy` 做快照，`COMMIT` 才真正落盘，`ROLLBACK` 还原快照。
5. **聚合**：识别到 `SELECT ... COUNT/SUM/AVG/...(expr)` 时进入聚合分支，全表归约成一行。

## 已知限制

- 单表查询，不支持 `JOIN`、`GROUP BY`、子查询、`IS NULL`
- 事务为可串行化级别（全表快照），并发由调用方保证
- 仅作为教学/玩具，请勿用于生产
