"""
PyDB - 纯 Python 实现、支持 SQL 子集的迷你关系数据库
========================================================

设计目标：用一份单文件代码，把「Lexer -> Parser -> Planner -> Executor -> Storage」
五层经典数据库架构讲清楚。仅依赖标准库。

支持的 SQL 子集
----------------
DDL  : CREATE TABLE name (col TYPE [PRIMARY KEY] [NOT NULL], ...)
       DROP TABLE name
       SHOW TABLES
       DESCRIBE name
DML  : INSERT INTO name [(c,c,...)] VALUES (...), (...)
       UPDATE name SET c = expr [, ...] [WHERE cond]
       DELETE FROM name [WHERE cond]
DQL  : SELECT [DISTINCT] col_or_expr [, ...] FROM name
         [WHERE cond] [ORDER BY col [ASC|DESC]] [LIMIT n]
事务 : BEGIN / COMMIT / ROLLBACK
聚合 : COUNT/SUM/AVG/MIN/MAX  (在 SELECT 中)
WHERE: 支持  AND / OR / NOT / = != < <= > >= LIKE / IN(...) 表达式
TYPE : INT / FLOAT / TEXT / BOOL

存储
----
单 JSON 文件持久化，事务用「内存快照 + 提交时落盘」模式。

用法
----
    python pydb.py demo                  # 一键演示
    python pydb.py shell mydb.json       # 进入交互 shell
"""

from __future__ import annotations

import json
import re
import sys
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ============================================================================
# 1. Lexer —— 纯正则 + 手工状态机
# ============================================================================
KEYWORDS = {
    "SELECT", "FROM", "WHERE", "INSERT", "INTO", "VALUES", "UPDATE",
    "SET", "DELETE", "CREATE", "TABLE", "DROP", "AND", "OR", "NOT",
    "IN", "LIKE", "ORDER", "BY", "ASC", "DESC", "LIMIT", "DISTINCT",
    "PRIMARY", "KEY", "NULL", "INT", "FLOAT", "TEXT", "BOOL", "TRUE",
    "FALSE", "BEGIN", "COMMIT", "ROLLBACK", "SHOW", "TABLES",
    "DESCRIBE", "AS",
}

TOKEN_RE = re.compile(
    r"""
    (\s+)                                # 1 whitespace (skip)
  | (--[^\n]*)                           # 2 comment
  | '((?:[^']|'')*)'                     # 3 string
  | (\d+\.\d+|\d+)                       # 4 number
  | (<=|>=|!=|<>|<|>|=|\(|\)|,|\*|;)     # 5 punct/op
  | ([A-Za-z_][A-Za-z0-9_]*)             # 6 ident/kw
  | (.)                                  # 7 unknown
""",
    re.VERBOSE,
)


def tokenize(sql: str) -> list[tuple[str, Any]]:
    out: list[tuple[str, Any]] = []
    pos = 0
    while pos < len(sql):
        m = TOKEN_RE.match(sql, pos)
        if not m:
            raise SyntaxError(f"bad char at {pos}: {sql[pos]!r}")
        pos = m.end()
        ws, comment, s, num, op, ident, bad = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5), m.group(6), m.group(7)
        if ws is not None or comment is not None:
            continue
        if s is not None:
            out.append(("STR", s.replace("''", "'")))
        elif num is not None:
            out.append(("NUM", float(num) if "." in num else int(num)))
        elif op is not None:
            out.append((op, op))
        elif ident is not None:
            up = ident.upper()
            if up in KEYWORDS:
                out.append((up, up))
            else:
                out.append(("ID", ident))
        elif bad is not None:
            raise SyntaxError(f"unexpected token: {bad!r}")
    out.append(("EOF", None))
    return out


# ============================================================================
# 2. AST nodes
# ============================================================================
@dataclass
class Column:
    name: str
    type: str
    primary: bool = False
    not_null: bool = False


@dataclass
class CreateTable:
    name: str
    columns: list[Column]


@dataclass
class DropTable:
    name: str


@dataclass
class ShowTables:
    pass


@dataclass
class Describe:
    name: str


@dataclass
class Insert:
    table: str
    columns: list[str] | None
    rows: list[list[Any]]


@dataclass
class Update:
    table: str
    sets: list[tuple[str, Any]]
    where: Any


@dataclass
class Delete:
    table: str
    where: Any


@dataclass
class Select:
    table: str
    columns: list[Any]            # list of expr or ('*',)
    aliases: list[str | None]
    distinct: bool
    where: Any
    order_by: tuple[str, str] | None
    limit: int | None


# ============================================================================
# 3. Parser —— 递归下降
# ============================================================================
class Parser:
    def __init__(self, toks: list[tuple[str, Any]]):
        self.toks = toks
        self.i = 0

    # helpers ---------------------------------------------------------------
    def peek(self, off: int = 0) -> tuple[str, Any]:
        return self.toks[self.i + off]

    def eat(self, *kinds: str) -> tuple[str, Any]:
        t = self.toks[self.i]
        if kinds and t[0] not in kinds:
            raise SyntaxError(f"expected {kinds}, got {t}")
        self.i += 1
        return t

    def accept(self, *kinds: str) -> tuple[str, Any] | None:
        if self.toks[self.i][0] in kinds:
            return self.eat()
        return None

    # entry -----------------------------------------------------------------
    def parse(self):
        t = self.peek()[0]
        if t == "CREATE":
            return self.create()
        if t == "DROP":
            return self.drop()
        if t == "SHOW":
            self.eat()
            self.eat("TABLES")
            return ShowTables()
        if t == "DESCRIBE":
            self.eat()
            return Describe(self.eat("ID")[1])
        if t == "INSERT":
            return self.insert()
        if t == "UPDATE":
            return self.update()
        if t == "DELETE":
            return self.delete()
        if t == "SELECT":
            return self.select()
        if t in ("BEGIN", "COMMIT", "ROLLBACK"):
            return ("TX", self.eat()[0])
        raise SyntaxError(f"unknown stmt: {t}")

    # DDL -------------------------------------------------------------------
    def create(self):
        self.eat("CREATE")
        self.eat("TABLE")
        name = self.eat("ID")[1]
        self.eat("(")
        cols = []
        while True:
            cname = self.eat("ID")[1]
            ctype = self.eat("INT", "FLOAT", "TEXT", "BOOL")[0]
            primary = False
            not_null = False
            while True:
                if self.accept("PRIMARY"):
                    self.eat("KEY")
                    primary = True
                    not_null = True
                elif self.accept("NOT"):
                    self.eat("NULL")
                    not_null = True
                else:
                    break
            cols.append(Column(cname, ctype, primary, not_null))
            if not self.accept(","):
                break
        self.eat(")")
        return CreateTable(name, cols)

    def drop(self):
        self.eat("DROP")
        self.eat("TABLE")
        return DropTable(self.eat("ID")[1])

    # DML -------------------------------------------------------------------
    def insert(self):
        self.eat("INSERT")
        self.eat("INTO")
        table = self.eat("ID")[1]
        cols = None
        if self.accept("("):
            cols = [self.eat("ID")[1]]
            while self.accept(","):
                cols.append(self.eat("ID")[1])
            self.eat(")")
        self.eat("VALUES")
        rows = [self._values()]
        while self.accept(","):
            rows.append(self._values())
        return Insert(table, cols, rows)

    def _values(self) -> list[Any]:
        self.eat("(")
        vs = [self.literal()]
        while self.accept(","):
            vs.append(self.literal())
        self.eat(")")
        return vs

    def literal(self):
        t = self.eat()
        if t[0] == "STR":
            return t[1]
        if t[0] == "NUM":
            return t[1]
        if t[0] == "TRUE":
            return True
        if t[0] == "FALSE":
            return False
        if t[0] == "NULL":
            return None
        raise SyntaxError(f"literal expected, got {t}")

    def update(self):
        self.eat("UPDATE")
        table = self.eat("ID")[1]
        self.eat("SET")
        sets = []
        while True:
            col = self.eat("ID")[1]
            self.eat("=")
            sets.append((col, self.expr()))
            if not self.accept(","):
                break
        where = None
        if self.accept("WHERE"):
            where = self.expr()
        return Update(table, sets, where)

    def delete(self):
        self.eat("DELETE")
        self.eat("FROM")
        table = self.eat("ID")[1]
        where = None
        if self.accept("WHERE"):
            where = self.expr()
        return Delete(table, where)

    # SELECT ----------------------------------------------------------------
    def select(self):
        self.eat("SELECT")
        distinct = bool(self.accept("DISTINCT"))
        cols, aliases = [], []
        if self.accept("*"):
            cols.append(("*",))
            aliases.append(None)
        else:
            cols.append(self.expr())
            aliases.append(self._alias())
            while self.accept(","):
                cols.append(self.expr())
                aliases.append(self._alias())
        self.eat("FROM")
        table = self.eat("ID")[1]
        where = None
        if self.accept("WHERE"):
            where = self.expr()
        order_by = None
        if self.accept("ORDER"):
            self.eat("BY")
            col = self.eat("ID")[1]
            direction = "ASC"
            if self.accept("DESC"):
                direction = "DESC"
            else:
                self.accept("ASC")
            order_by = (col, direction)
        limit = None
        if self.accept("LIMIT"):
            limit = int(self.eat("NUM")[1])
        return Select(table, cols, aliases, distinct, where, order_by, limit)

    def _alias(self) -> str | None:
        if self.accept("AS"):
            return self.eat("ID")[1]
        if self.peek()[0] == "ID":
            # Bare identifier following expression = alias
            # Heuristic: treat as alias only if not followed by an operator that
            # could continue the expression (we already consumed full expr).
            return self.eat("ID")[1]
        return None

    # expression: OR > AND > NOT > comparison > primary --------------------
    def expr(self):
        return self._or()

    def _or(self):
        left = self._and()
        while self.accept("OR"):
            left = ("or", left, self._and())
        return left

    def _and(self):
        left = self._not()
        while self.accept("AND"):
            left = ("and", left, self._not())
        return left

    def _not(self):
        if self.accept("NOT"):
            return ("not", self._not())
        return self._cmp()

    def _cmp(self):
        left = self._add()
        t = self.peek()[0]
        if t in ("=", "!=", "<>", "<", "<=", ">", ">="):
            op = self.eat()[0]
            return (op if op != "<>" else "!=", left, self._add())
        if self.accept("LIKE"):
            return ("like", left, self._add())
        if self.accept("IN"):
            self.eat("(")
            vals = [self.literal()]
            while self.accept(","):
                vals.append(self.literal())
            self.eat(")")
            return ("in", left, vals)
        return left

    def _add(self):
        left = self._primary()
        while self.peek()[0] in ("+", "-"):
            # Not lexed as ops; skip arithmetic for simplicity
            break
        return left

    def _primary(self):
        t = self.peek()
        if t[0] == "(":
            self.eat()
            e = self.expr()
            self.eat(")")
            return e
        if t[0] in ("STR", "NUM"):
            return ("lit", self.eat()[1])
        if t[0] in ("TRUE", "FALSE"):
            self.eat()
            return ("lit", t[0] == "TRUE")
        if t[0] == "NULL":
            self.eat()
            return ("lit", None)
        if t[0] == "ID":
            name = self.eat()[1]
            # function call?
            if self.accept("("):
                if self.accept("*"):
                    self.eat(")")
                    return ("call", name.upper(), [("col", "*")])
                args = [self.expr()]
                while self.accept(","):
                    args.append(self.expr())
                self.eat(")")
                return ("call", name.upper(), args)
            return ("col", name)
        raise SyntaxError(f"unexpected {t}")


# ============================================================================
# 4. Storage
# ============================================================================
@dataclass
class Storage:
    path: Path
    tables: dict[str, dict] = field(default_factory=dict)
    # tables[name] = {"columns": [Column..], "rows": [[v,v,...]]}

    def load(self):
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.tables = {}
            for n, t in data.items():
                cols = [Column(**c) for c in t["columns"]]
                self.tables[n] = {"columns": cols, "rows": t["rows"]}

    def save(self):
        out = {}
        for n, t in self.tables.items():
            out[n] = {
                "columns": [c.__dict__ for c in t["columns"]],
                "rows": t["rows"],
            }
        self.path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")


# ============================================================================
# 5. Executor
# ============================================================================
class Executor:
    def __init__(self, storage: Storage):
        self.s = storage
        self.in_tx = False
        self.snapshot: dict | None = None

    # ----------------- expression eval over a row dict --------------------
    def eval_expr(self, e, row: dict) -> Any:
        op = e[0]
        if op == "lit":
            return e[1]
        if op == "col":
            if e[1] not in row:
                raise NameError(f"column {e[1]!r} not found")
            return row[e[1]]
        if op == "not":
            return not self.eval_expr(e[1], row)
        if op == "and":
            return self.eval_expr(e[1], row) and self.eval_expr(e[2], row)
        if op == "or":
            return self.eval_expr(e[1], row) or self.eval_expr(e[2], row)
        if op in ("=", "!=", "<", "<=", ">", ">="):
            a, b = self.eval_expr(e[1], row), self.eval_expr(e[2], row)
            if a is None or b is None:
                return False
            return {"=": a == b, "!=": a != b, "<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b}[op]
        if op == "like":
            a = self.eval_expr(e[1], row)
            pat = self.eval_expr(e[2], row)
            if a is None or pat is None:
                return False
            regex_parts = []
            for ch in str(pat):
                if ch == "%":
                    regex_parts.append(".*")
                elif ch == "_":
                    regex_parts.append(".")
                else:
                    regex_parts.append(re.escape(ch))
            regex = "^" + "".join(regex_parts) + "$"
            return re.match(regex, str(a)) is not None
        if op == "in":
            a = self.eval_expr(e[1], row)
            return a in e[2]
        if op == "call":
            # Aggregation handled at SELECT level; here we only support pass-through
            # if used inside WHERE, treat as scalar: e.g. UPPER -> just return arg
            fn, args = e[1], e[2]
            vs = [self.eval_expr(a, row) for a in args]
            if fn == "UPPER":
                return str(vs[0]).upper() if vs[0] is not None else None
            if fn == "LOWER":
                return str(vs[0]).lower() if vs[0] is not None else None
            if fn == "LEN" or fn == "LENGTH":
                return len(str(vs[0])) if vs[0] is not None else None
            raise NameError(f"unknown function {fn}")
        raise RuntimeError(f"bad expr {e}")

    # ------------------------------- statements ---------------------------
    def execute(self, ast):
        if isinstance(ast, tuple) and ast[0] == "TX":
            return self.tx(ast[1])
        meth = {
            CreateTable: self.do_create,
            DropTable: self.do_drop,
            ShowTables: lambda a: ("table", ["table"], [[n] for n in self.s.tables]),
            Describe: self.do_describe,
            Insert: self.do_insert,
            Update: self.do_update,
            Delete: self.do_delete,
            Select: self.do_select,
        }[type(ast)]
        return meth(ast)

    def tx(self, kind: str):
        if kind == "BEGIN":
            if self.in_tx:
                raise RuntimeError("already in transaction")
            self.snapshot = deepcopy(self.s.tables)
            self.in_tx = True
            return ("ok", "BEGIN")
        if kind == "COMMIT":
            if not self.in_tx:
                raise RuntimeError("no active tx")
            self.snapshot = None
            self.in_tx = False
            self.s.save()
            return ("ok", "COMMIT")
        if kind == "ROLLBACK":
            if not self.in_tx:
                raise RuntimeError("no active tx")
            self.s.tables = self.snapshot or {}
            self.snapshot = None
            self.in_tx = False
            return ("ok", "ROLLBACK")
        raise RuntimeError(kind)

    def _autosave(self):
        if not self.in_tx:
            self.s.save()

    def do_create(self, a: CreateTable):
        if a.name in self.s.tables:
            raise RuntimeError(f"table exists: {a.name}")
        self.s.tables[a.name] = {"columns": a.columns, "rows": []}
        self._autosave()
        return ("ok", f"CREATE TABLE {a.name}")

    def do_drop(self, a: DropTable):
        if a.name not in self.s.tables:
            raise RuntimeError(f"no such table: {a.name}")
        self.s.tables.pop(a.name)
        self._autosave()
        return ("ok", f"DROP TABLE {a.name}")

    def do_describe(self, a: Describe):
        if a.name not in self.s.tables:
            raise RuntimeError(f"no such table: {a.name}")
        cols = self.s.tables[a.name]["columns"]
        rows = [[c.name, c.type, "YES" if not c.not_null else "NO",
                 "PRI" if c.primary else ""] for c in cols]
        return ("table", ["Field", "Type", "Null", "Key"], rows)

    def _coerce(self, v: Any, col: Column):
        if v is None:
            if col.not_null:
                raise RuntimeError(f"column {col.name} cannot be null")
            return None
        if col.type == "INT":
            return int(v)
        if col.type == "FLOAT":
            return float(v)
        if col.type == "BOOL":
            return bool(v)
        if col.type == "TEXT":
            return str(v)
        return v

    def do_insert(self, a: Insert):
        t = self.s.tables.get(a.table)
        if t is None:
            raise RuntimeError(f"no such table: {a.table}")
        cols = t["columns"]
        col_names = [c.name for c in cols]
        target = a.columns or col_names
        for vals in a.rows:
            if len(vals) != len(target):
                raise RuntimeError("value count mismatch")
            row = [None] * len(cols)
            for col_name, v in zip(target, vals):
                if col_name not in col_names:
                    raise RuntimeError(f"unknown column: {col_name}")
                idx = col_names.index(col_name)
                row[idx] = self._coerce(v, cols[idx])
            # primary key check
            for i, c in enumerate(cols):
                if c.primary:
                    if any(r[i] == row[i] for r in t["rows"]):
                        raise RuntimeError(f"duplicate primary key on {c.name}")
                if c.not_null and row[i] is None:
                    raise RuntimeError(f"column {c.name} cannot be null")
            t["rows"].append(row)
        self._autosave()
        return ("ok", f"{len(a.rows)} row(s) inserted")

    def _row_dict(self, t: dict, row: list) -> dict:
        return {c.name: v for c, v in zip(t["columns"], row)}

    def do_update(self, a: Update):
        t = self.s.tables.get(a.table)
        if t is None:
            raise RuntimeError(f"no such table: {a.table}")
        cols = t["columns"]
        names = [c.name for c in cols]
        n = 0
        for row in t["rows"]:
            d = self._row_dict(t, row)
            if a.where and not self.eval_expr(a.where, d):
                continue
            for col, expr in a.sets:
                if col not in names:
                    raise RuntimeError(f"unknown column: {col}")
                idx = names.index(col)
                row[idx] = self._coerce(self.eval_expr(expr, d), cols[idx])
            n += 1
        self._autosave()
        return ("ok", f"{n} row(s) updated")

    def do_delete(self, a: Delete):
        t = self.s.tables.get(a.table)
        if t is None:
            raise RuntimeError(f"no such table: {a.table}")
        before = len(t["rows"])
        t["rows"] = [r for r in t["rows"]
                     if a.where and not self.eval_expr(a.where, self._row_dict(t, r))]
        if a.where is None:
            t["rows"] = []
        n = before - len(t["rows"])
        self._autosave()
        return ("ok", f"{n} row(s) deleted")

    # ------------------------- SELECT -------------------------------------
    AGG = {"COUNT", "SUM", "AVG", "MIN", "MAX"}

    def do_select(self, a: Select):
        t = self.s.tables.get(a.table)
        if t is None:
            raise RuntimeError(f"no such table: {a.table}")
        cols = t["columns"]
        names = [c.name for c in cols]

        # 1) where
        rows = []
        for r in t["rows"]:
            d = self._row_dict(t, r)
            if a.where is None or self.eval_expr(a.where, d):
                rows.append(d)

        # 2) order by
        if a.order_by:
            col, direction = a.order_by
            if col not in names:
                raise RuntimeError(f"unknown order col: {col}")
            rows.sort(key=lambda r: (r[col] is None, r[col]),
                      reverse=(direction == "DESC"))

        # 3) projection (with aggregation detection)
        is_agg = any(isinstance(c, tuple) and c[0] == "call" and c[1] in self.AGG
                     for c in a.columns if c != ("*",))
        if is_agg:
            out_row = []
            headers = []
            for col_expr, alias in zip(a.columns, a.aliases):
                if col_expr == ("*",):
                    raise RuntimeError("cannot mix * with aggregation")
                if col_expr[0] != "call" or col_expr[1] not in self.AGG:
                    raise RuntimeError("non-aggregate column in aggregate query")
                fn, args = col_expr[1], col_expr[2]
                vals = []
                for r in rows:
                    if args[0] == ("col", "*"):
                        vals.append(1)
                    else:
                        vals.append(self.eval_expr(args[0], r))
                vals = [v for v in vals if v is not None] if fn != "COUNT" else vals
                if fn == "COUNT":
                    out_row.append(len(vals))
                elif fn == "SUM":
                    out_row.append(sum(vals))
                elif fn == "AVG":
                    out_row.append(sum(vals) / len(vals) if vals else None)
                elif fn == "MIN":
                    out_row.append(min(vals) if vals else None)
                elif fn == "MAX":
                    out_row.append(max(vals) if vals else None)
                headers.append(alias or f"{fn}({self._expr_str(args[0])})")
            return ("table", headers, [out_row])

        # plain projection
        out_rows = []
        if len(a.columns) == 1 and a.columns[0] == ("*",):
            headers = list(names)
            for r in rows:
                out_rows.append([r[n] for n in names])
        else:
            headers = []
            for col_expr, alias in zip(a.columns, a.aliases):
                headers.append(alias or self._expr_str(col_expr))
            for r in rows:
                out_rows.append([self.eval_expr(c, r) for c in a.columns])

        if a.distinct:
            seen = set()
            uniq = []
            for r in out_rows:
                key = tuple(r)
                if key not in seen:
                    seen.add(key)
                    uniq.append(r)
            out_rows = uniq

        if a.limit is not None:
            out_rows = out_rows[:a.limit]
        return ("table", headers, out_rows)

    @staticmethod
    def _expr_str(e) -> str:
        if e[0] == "col":
            return e[1]
        if e[0] == "lit":
            return repr(e[1])
        if e[0] == "call":
            return f"{e[1]}({','.join(Executor._expr_str(a) for a in e[2])})"
        return "?"


# ============================================================================
# 6. Pretty printer
# ============================================================================
def render_table(headers: list[str], rows: list[list[Any]]) -> str:
    cells = [[("" if v is None else str(v)) for v in row] for row in rows]
    widths = [len(h) for h in headers]
    for r in cells:
        for i, c in enumerate(r):
            widths[i] = max(widths[i], len(c))
    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    out = [sep, "| " + " | ".join(h.ljust(w) for h, w in zip(headers, widths)) + " |", sep]
    for r in cells:
        out.append("| " + " | ".join(c.ljust(w) for c, w in zip(r, widths)) + " |")
    out.append(sep)
    out.append(f"{len(rows)} row(s)")
    return "\n".join(out)


# ============================================================================
# 7. Public API + REPL
# ============================================================================
class Database:
    def __init__(self, path: str | Path):
        self.storage = Storage(Path(path))
        self.storage.load()
        self.executor = Executor(self.storage)

    def run(self, sql: str):
        results = []
        for stmt in self._split(sql):
            stmt = stmt.strip()
            if not stmt:
                continue
            ast = Parser(tokenize(stmt)).parse()
            results.append(self.executor.execute(ast))
        return results[-1] if results else None

    @staticmethod
    def _split(sql: str) -> list[str]:
        # naive ; splitter that respects strings
        out, buf, in_str = [], [], False
        for ch in sql:
            if ch == "'":
                in_str = not in_str
                buf.append(ch)
            elif ch == ";" and not in_str:
                out.append("".join(buf))
                buf = []
            else:
                buf.append(ch)
        if buf:
            out.append("".join(buf))
        return out


def shell(path: str = "pydb.json"):
    db = Database(path)
    print(f"PyDB shell (db={path}). Type SQL ending with ';'. Ctrl+C to quit.")
    buf = ""
    while True:
        try:
            line = input("pydb> " if not buf else "  ...> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return
        buf += " " + line
        if ";" not in line:
            continue
        try:
            res = db.run(buf)
            if res is None:
                pass
            elif res[0] == "ok":
                print(res[1])
            elif res[0] == "table":
                print(render_table(res[1], res[2]))
        except Exception as e:  # noqa: BLE001
            print(f"ERROR: {e}")
        buf = ""


def demo():
    p = Path("./_pydb_demo.json")
    if p.exists():
        p.unlink()
    db = Database(p)

    sqls = [
        "CREATE TABLE users (id INT PRIMARY KEY, name TEXT NOT NULL, age INT, score FLOAT);",
        "INSERT INTO users VALUES (1, 'alice', 30, 95.5), (2, 'bob', 25, 80.0), (3, 'carol', 28, 88.0);",
        "INSERT INTO users (id, name, age) VALUES (4, 'dave', 35);",
        "SELECT * FROM users;",
        "SELECT name, score FROM users WHERE age >= 28 ORDER BY score DESC;",
        "SELECT COUNT(*) AS n, AVG(score) AS avg_s FROM users WHERE score >= 0;",
        "BEGIN;",
        "UPDATE users SET score = 100 WHERE name = 'alice';",
        "SELECT name, score FROM users WHERE name = 'alice';",
        "ROLLBACK;",
        "SELECT name, score FROM users WHERE name = 'alice';",
        "DELETE FROM users WHERE age > 30;",
        "SHOW TABLES;",
        "DESCRIBE users;",
        "SELECT name FROM users WHERE name LIKE 'a%';",
        "SELECT name FROM users WHERE id IN (1, 2);",
    ]
    for s in sqls:
        print(f"\n>>> {s.strip()}")
        try:
            res = db.run(s)
            if res is None:
                continue
            if res[0] == "ok":
                print(res[1])
            else:
                print(render_table(res[1], res[2]))
        except Exception as e:  # noqa: BLE001
            print(f"ERROR: {e}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd == "demo":
        demo()
    elif cmd == "shell":
        shell(sys.argv[2] if len(sys.argv) > 2 else "pydb.json")
    else:
        print("usage: pydb.py demo | shell [file]")


if __name__ == "__main__":
    main()
