"""
PyVM - 纯 Python 实现的栈式虚拟机（执行字节码）
=================================================

本项目演示一台经典「栈式虚拟机」的完整链路：

    源码 (mini lang) ──Lexer──▶ AST ──Compiler──▶ 字节码 ──VM──▶ 结果

虚拟机层面与 Python / Java / Lua 字节码 VM 同构：
  - 一个值栈 (operand stack)
  - 调用栈 (frames)，每帧含 局部变量 / 字节码指针 / 返回地址
  - 常量池 / 名称池
  - 指令集（见下方 INSTRS）

所有代码用 Python 标准库实现，单文件 ~700 行，运行：

    python pyvm.py demo                # 跑内置 demo（编译 + 反汇编 + 执行）
    python pyvm.py run script.pv       # 编译并执行源代码
    python pyvm.py asm script.pv       # 只输出反汇编
    python pyvm.py vm bytecode.json    # 直接加载字节码 JSON 并执行

源语言（pv）特性
----------------
  - 数字 / 字符串 / 布尔 / nil
  - `let`, 算术、比较、逻辑、`if/else`、`while`、`for`
  - `fn name(a,b) { ... return ...; }`，递归 + 闭包变量（通过 free upvalue 简化为顶层捕获）
  - 内置 print / len
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from typing import Any


# ============================================================================
# 1. 字节码指令集
# ============================================================================
# 每条指令: (OPNAME, [arg]) ; arg 为整数索引或立即数。
INSTRS = [
    "LOAD_CONST",   # push consts[arg]
    "LOAD_NAME",    # push globals[names[arg]]
    "STORE_NAME",   # globals[names[arg]] = pop()
    "LOAD_LOCAL",   # push frame.locals[arg]
    "STORE_LOCAL",  # frame.locals[arg] = pop()
    "POP",          # pop and discard
    "DUP",          # duplicate TOS
    "BIN_ADD", "BIN_SUB", "BIN_MUL", "BIN_DIV", "BIN_MOD",
    "CMP_EQ", "CMP_NE", "CMP_LT", "CMP_LE", "CMP_GT", "CMP_GE",
    "UNARY_NEG", "UNARY_NOT",
    "JUMP",         # unconditional, arg = absolute target
    "JUMP_IF_FALSE",
    "JUMP_IF_TRUE",
    "CALL",         # arg = nargs ; pops fn + args, pushes result
    "RETURN",       # pop value, restore frame
    "MAKE_LIST",    # arg = n; pop n, push list
    "INDEX_GET",    # tos = pop(); container = pop(); push container[tos]
    "INDEX_SET",    # value = pop(); index = pop(); container = pop(); container[index]=value
    "PRINT",        # arg = n; pop n and print
    "BUILD_FUNC",   # arg = consts idx -> CodeObject; push Function
    "HALT",
]


# ============================================================================
# 2. 编译期数据：CodeObject
# ============================================================================
@dataclass
class CodeObject:
    name: str
    nparams: int
    nlocals: int
    code: list[tuple]                          # [(op, arg), ...]
    consts: list[Any] = field(default_factory=list)
    names:  list[str] = field(default_factory=list)
    local_names: list[str] = field(default_factory=list)

    def to_json(self):
        return {
            "name": self.name,
            "nparams": self.nparams,
            "nlocals": self.nlocals,
            "code": [[op, arg] for op, arg in self.code],
            "consts": [_const_to_json(c) for c in self.consts],
            "names": self.names,
            "local_names": self.local_names,
        }

    @staticmethod
    def from_json(d: dict) -> "CodeObject":
        consts = [_const_from_json(c) for c in d["consts"]]
        return CodeObject(
            name=d["name"], nparams=d["nparams"], nlocals=d["nlocals"],
            code=[tuple(x) for x in d["code"]],
            consts=consts, names=d["names"], local_names=d["local_names"],
        )


def _const_to_json(c):
    if isinstance(c, CodeObject):
        return {"__code__": True, **c.to_json()}
    return c


def _const_from_json(v):
    if isinstance(v, dict) and v.get("__code__"):
        return CodeObject.from_json(v)
    return v


# ============================================================================
# 3. Lexer + Parser  （与 PyLang 同构，最小化版本）
# ============================================================================
KEYWORDS = {"let", "fn", "return", "if", "else", "while", "for",
            "true", "false", "nil", "break", "continue", "print"}
DOUBLE = {"==", "!=", "<=", ">=", "&&", "||"}


class Tok:
    __slots__ = ("k", "v", "ln")
    def __init__(self, k, v, ln):
        self.k = k; self.v = v; self.ln = ln
    def __repr__(self):
        return f"<{self.k}:{self.v}>"


def tokenize(src: str) -> list[Tok]:
    out, i, n, line = [], 0, len(src), 1
    while i < n:
        c = src[i]
        if c == "\n":
            line += 1; i += 1; continue
        if c.isspace():
            i += 1; continue
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            while i < n and src[i] != "\n":
                i += 1
            continue
        if c == '"':
            j = i + 1; buf = []
            while j < n and src[j] != '"':
                if src[j] == "\\" and j + 1 < n:
                    buf.append({"n": "\n", "t": "\t", "\\": "\\", '"': '"'}.get(src[j + 1], src[j + 1]))
                    j += 2
                else:
                    buf.append(src[j]); j += 1
            if j >= n: raise SyntaxError(f"unterminated string at line {line}")
            out.append(Tok("STR", "".join(buf), line)); i = j + 1; continue
        if c.isdigit():
            j = i
            while j < n and (src[j].isdigit() or src[j] == "."):
                j += 1
            num = src[i:j]
            out.append(Tok("NUM", float(num) if "." in num else int(num), line))
            i = j; continue
        if c.isalpha() or c == "_":
            j = i
            while j < n and (src[j].isalnum() or src[j] == "_"):
                j += 1
            ident = src[i:j]
            out.append(Tok(ident if ident in KEYWORDS else "ID", ident, line))
            i = j; continue
        if i + 1 < n and src[i:i + 2] in DOUBLE:
            out.append(Tok(src[i:i + 2], src[i:i + 2], line)); i += 2; continue
        if c in "+-*/%(){}[];,<>=!":
            out.append(Tok(c, c, line)); i += 1; continue
        raise SyntaxError(f"unexpected {c!r} at line {line}")
    out.append(Tok("EOF", None, line))
    return out


# AST nodes
@dataclass
class Num: v: Any
@dataclass
class Str_: v: str
@dataclass
class Bool_: v: bool
@dataclass
class Nil_: pass
@dataclass
class Var:  name: str
@dataclass
class List_: items: list
@dataclass
class Idx: obj: Any; idx: Any
@dataclass
class BinOp: op: str; l: Any; r: Any
@dataclass
class Un: op: str; x: Any
@dataclass
class Call: f: Any; args: list
@dataclass
class Assign: tgt: Any; v: Any
@dataclass
class Let:  name: str; v: Any
@dataclass
class FnDecl: name: str; params: list; body: list
@dataclass
class If:   c: Any; t: list; e: list
@dataclass
class While: c: Any; b: list
@dataclass
class For:  init: Any; c: Any; step: Any; b: list
@dataclass
class Return: v: Any
@dataclass
class Print:  args: list
@dataclass
class ExprStmt: v: Any


class Parser:
    PREC = {"||": 1, "&&": 2, "==": 3, "!=": 3,
            "<": 4, "<=": 4, ">": 4, ">=": 4,
            "+": 5, "-": 5, "*": 6, "/": 6, "%": 6}

    def __init__(self, toks):
        self.t = toks; self.i = 0
    def p(self, o=0): return self.t[self.i + o]
    def eat(self, *k):
        tk = self.t[self.i]
        if k and tk.k not in k:
            raise SyntaxError(f"expected {k}, got {tk.k!r} at line {tk.ln}")
        self.i += 1; return tk
    def acc(self, *k):
        return self.eat() if self.t[self.i].k in k else None

    def parse(self):
        prog = []
        while self.p().k != "EOF":
            prog.append(self.stmt())
        return prog

    def stmt(self):
        k = self.p().k
        if k == "let": return self.let_()
        if k == "fn": return self.fndecl()
        if k == "if": return self.if_()
        if k == "while": return self.while_()
        if k == "for": return self.for_()
        if k == "return":
            self.eat()
            v = None if self.p().k == ";" else self.expr()
            self.eat(";"); return Return(v if v is not None else Nil_())
        if k == "print":
            self.eat(); self.eat("(")
            args = []
            if self.p().k != ")":
                args.append(self.expr())
                while self.acc(","): args.append(self.expr())
            self.eat(")"); self.eat(";")
            return Print(args)
        e = self.expr(); self.eat(";"); return ExprStmt(e)

    def let_(self):
        self.eat("let"); name = self.eat("ID").v; self.eat("=")
        v = self.expr(); self.eat(";"); return Let(name, v)

    def fndecl(self):
        self.eat("fn"); name = self.eat("ID").v
        params = self.params(); body = self.block()
        return FnDecl(name, params, body)

    def params(self):
        self.eat("(")
        ps = []
        if self.p().k != ")":
            ps.append(self.eat("ID").v)
            while self.acc(","): ps.append(self.eat("ID").v)
        self.eat(")"); return ps

    def block(self):
        self.eat("{"); s = []
        while self.p().k != "}":
            s.append(self.stmt())
        self.eat("}"); return s

    def if_(self):
        self.eat("if"); self.eat("("); c = self.expr(); self.eat(")")
        t = self.block(); e = []
        if self.acc("else"):
            e = [self.if_()] if self.p().k == "if" else self.block()
        return If(c, t, e)

    def while_(self):
        self.eat("while"); self.eat("("); c = self.expr(); self.eat(")")
        b = self.block(); return While(c, b)

    def for_(self):
        self.eat("for"); self.eat("(")
        init = self.let_() if self.p().k == "let" else self._exprstmt()
        c = self.expr(); self.eat(";")
        step = self.expr(); self.eat(")")
        b = self.block(); return For(init, c, step, b)

    def _exprstmt(self):
        e = self.expr(); self.eat(";"); return ExprStmt(e)

    def expr(self):
        return self.assign()

    def assign(self):
        l = self.bin(1)
        if self.acc("="):
            r = self.assign()
            if not isinstance(l, (Var, Idx)):
                raise SyntaxError("bad assign target")
            return Assign(l, r)
        return l

    def bin(self, mp):
        l = self.un()
        while True:
            tk = self.p(); pr = self.PREC.get(tk.k, 0)
            if pr < mp: break
            op = self.eat().k
            r = self.bin(pr + 1)
            l = BinOp(op, l, r)
        return l

    def un(self):
        if self.acc("-"): return Un("-", self.un())
        if self.acc("!"): return Un("!", self.un())
        return self.post()

    def post(self):
        n = self.prim()
        while True:
            if self.acc("("):
                a = []
                if self.p().k != ")":
                    a.append(self.expr())
                    while self.acc(","): a.append(self.expr())
                self.eat(")")
                n = Call(n, a)
            elif self.acc("["):
                ix = self.expr(); self.eat("]"); n = Idx(n, ix)
            else:
                break
        return n

    def prim(self):
        tk = self.p()
        if tk.k == "NUM": self.eat(); return Num(tk.v)
        if tk.k == "STR": self.eat(); return Str_(tk.v)
        if tk.k == "true": self.eat(); return Bool_(True)
        if tk.k == "false": self.eat(); return Bool_(False)
        if tk.k == "nil": self.eat(); return Nil_()
        if tk.k == "ID": self.eat(); return Var(tk.v)
        if tk.k == "(":
            self.eat(); e = self.expr(); self.eat(")"); return e
        if tk.k == "[":
            self.eat(); items = []
            if self.p().k != "]":
                items.append(self.expr())
                while self.acc(","): items.append(self.expr())
            self.eat("]"); return List_(items)
        raise SyntaxError(f"unexpected token {tk.k!r} at line {tk.ln}")


# ============================================================================
# 4. Compiler  (AST -> bytecode)
# ============================================================================
class Compiler:
    def __init__(self, name: str, params: list[str] | None = None,
                 outer: "Compiler | None" = None):
        self.name = name
        self.params = params or []
        self.outer = outer
        self.code: list[tuple] = []
        self.consts: list = []
        self.names: list[str] = []
        self.locals: list[str] = list(self.params)  # 参数也是局部
        self.is_function = outer is not None

    # helpers ------------------------------------------------------------
    def emit(self, op, arg=0) -> int:
        self.code.append((op, arg))
        return len(self.code) - 1

    def patch(self, pos: int, arg: int):
        op = self.code[pos][0]
        self.code[pos] = (op, arg)

    def const(self, v) -> int:
        for i, c in enumerate(self.consts):
            if type(c) is type(v) and c == v and not isinstance(c, CodeObject):
                return i
        self.consts.append(v)
        return len(self.consts) - 1

    def name_idx(self, nm: str) -> int:
        if nm in self.names: return self.names.index(nm)
        self.names.append(nm); return len(self.names) - 1

    def local_idx(self, nm: str) -> int:
        if nm in self.locals: return self.locals.index(nm)
        self.locals.append(nm); return len(self.locals) - 1

    # main ---------------------------------------------------------------
    def compile_program(self, prog: list) -> CodeObject:
        for s in prog:
            self.stmt(s)
        self.emit("HALT")
        return CodeObject(
            name=self.name, nparams=len(self.params), nlocals=len(self.locals),
            code=self.code, consts=self.consts, names=self.names,
            local_names=self.locals,
        )

    def compile_function(self, fd: FnDecl) -> CodeObject:
        for s in fd.body:
            self.stmt(s)
        # implicit return nil
        self.emit("LOAD_CONST", self.const(None))
        self.emit("RETURN")
        return CodeObject(
            name=fd.name, nparams=len(fd.params), nlocals=len(self.locals),
            code=self.code, consts=self.consts, names=self.names,
            local_names=self.locals,
        )

    # stmt ---------------------------------------------------------------
    def stmt(self, s):
        if isinstance(s, Let):
            self.expr(s.v)
            if self.is_function:
                self.emit("STORE_LOCAL", self.local_idx(s.name))
            else:
                self.emit("STORE_NAME", self.name_idx(s.name))
        elif isinstance(s, ExprStmt):
            self.expr(s.v); self.emit("POP")
        elif isinstance(s, Print):
            for a in s.args:
                self.expr(a)
            self.emit("PRINT", len(s.args))
        elif isinstance(s, Return):
            self.expr(s.v); self.emit("RETURN")
        elif isinstance(s, If):
            self.expr(s.c)
            jf = self.emit("JUMP_IF_FALSE", 0)
            for st in s.t: self.stmt(st)
            jend = self.emit("JUMP", 0)
            self.patch(jf, len(self.code))
            for st in s.e: self.stmt(st)
            self.patch(jend, len(self.code))
        elif isinstance(s, While):
            top = len(self.code)
            self.expr(s.c)
            jf = self.emit("JUMP_IF_FALSE", 0)
            for st in s.b: self.stmt(st)
            self.emit("JUMP", top)
            self.patch(jf, len(self.code))
        elif isinstance(s, For):
            self.stmt(s.init)
            top = len(self.code)
            self.expr(s.c)
            jf = self.emit("JUMP_IF_FALSE", 0)
            for st in s.b: self.stmt(st)
            self.expr(s.step); self.emit("POP")
            self.emit("JUMP", top)
            self.patch(jf, len(self.code))
        elif isinstance(s, FnDecl):
            sub = Compiler(s.name, s.params, outer=self)
            code_obj = sub.compile_function(s)
            ci = self.const(code_obj)
            self.emit("BUILD_FUNC", ci)
            if self.is_function:
                self.emit("STORE_LOCAL", self.local_idx(s.name))
            else:
                self.emit("STORE_NAME", self.name_idx(s.name))
        else:
            raise RuntimeError(f"bad stmt: {s}")

    # expr ---------------------------------------------------------------
    def expr(self, e):
        if isinstance(e, Num):  self.emit("LOAD_CONST", self.const(e.v)); return
        if isinstance(e, Str_): self.emit("LOAD_CONST", self.const(e.v)); return
        if isinstance(e, Bool_):self.emit("LOAD_CONST", self.const(e.v)); return
        if isinstance(e, Nil_): self.emit("LOAD_CONST", self.const(None)); return
        if isinstance(e, Var):
            self.load_var(e.name); return
        if isinstance(e, List_):
            for it in e.items: self.expr(it)
            self.emit("MAKE_LIST", len(e.items)); return
        if isinstance(e, Idx):
            self.expr(e.obj); self.expr(e.idx); self.emit("INDEX_GET"); return
        if isinstance(e, Un):
            self.expr(e.x)
            self.emit("UNARY_NEG" if e.op == "-" else "UNARY_NOT"); return
        if isinstance(e, BinOp):
            self.binop(e); return
        if isinstance(e, Call):
            self.expr(e.f)
            for a in e.args: self.expr(a)
            self.emit("CALL", len(e.args)); return
        if isinstance(e, Assign):
            if isinstance(e.tgt, Var):
                self.expr(e.v)
                self.emit("DUP")  # leave value on stack as expression result
                self.store_var(e.tgt.name)
            elif isinstance(e.tgt, Idx):
                # emit: container, index, value, INDEX_SET ; INDEX_SET leaves value on stack
                self.expr(e.tgt.obj)
                self.expr(e.tgt.idx)
                self.expr(e.v)
                self.emit("INDEX_SET")
            return
        raise RuntimeError(f"bad expr {e}")

    # Variable load/store: search locals (if function) -> globals
    def load_var(self, name: str):
        if self.is_function and name in self.locals:
            self.emit("LOAD_LOCAL", self.locals.index(name))
        else:
            self.emit("LOAD_NAME", self.name_idx(name))

    def store_var(self, name: str):
        if self.is_function and name in self.locals:
            self.emit("STORE_LOCAL", self.locals.index(name))
        elif self.is_function and name not in self.locals and name in self.outer_globals():
            # 全局名直接 store 到全局
            self.emit("STORE_NAME", self.name_idx(name))
        elif self.is_function:
            # 在函数体内首次写入但未声明 -> 当作局部
            self.emit("STORE_LOCAL", self.local_idx(name))
        else:
            self.emit("STORE_NAME", self.name_idx(name))

    def outer_globals(self) -> set[str]:
        c = self.outer
        seen: set[str] = set()
        while c is not None:
            seen.update(c.names)
            c = c.outer
        return seen

    def binop(self, e: BinOp):
        if e.op == "&&":
            # 短路
            self.expr(e.l)
            self.emit("DUP")
            jf = self.emit("JUMP_IF_FALSE", 0)
            self.emit("POP")          # discard the truthy lhs
            self.expr(e.r)
            self.patch(jf, len(self.code))
            return
        if e.op == "||":
            self.expr(e.l)
            self.emit("DUP")
            jt = self.emit("JUMP_IF_TRUE", 0)
            self.emit("POP")
            self.expr(e.r)
            self.patch(jt, len(self.code))
            return
        self.expr(e.l); self.expr(e.r)
        OP = {
            "+": "BIN_ADD", "-": "BIN_SUB", "*": "BIN_MUL", "/": "BIN_DIV", "%": "BIN_MOD",
            "==": "CMP_EQ", "!=": "CMP_NE",
            "<": "CMP_LT", "<=": "CMP_LE", ">": "CMP_GT", ">=": "CMP_GE",
        }[e.op]
        self.emit(OP)


# ============================================================================
# 5. VM
# ============================================================================
@dataclass
class Function:
    code: CodeObject
    def __repr__(self): return f"<fn {self.code.name}/{self.code.nparams}>"


@dataclass
class Frame:
    code: CodeObject
    pc: int = 0
    locals: list = field(default_factory=list)


class VM:
    def __init__(self, debug: bool = False):
        self.globals: dict[str, Any] = {
            "len": _builtin("len", lambda x: len(x) if x is not None else 0),
            "type": _builtin("type", _typeof),
            "str":  _builtin("str", _strify),
            "num":  _builtin("num", _numify),
        }
        self.debug = debug

    def run(self, top: CodeObject) -> Any:
        frame = Frame(code=top, pc=0, locals=[None] * top.nlocals)
        stack: list = []
        frames: list[Frame] = [frame]

        while frames:
            f = frames[-1]
            if f.pc >= len(f.code.code):
                frames.pop()
                continue
            op, arg = f.code.code[f.pc]
            if self.debug:
                print(f"[{f.code.name}@{f.pc:03d}] {op} {arg}  stack={stack[-3:]}")
            f.pc += 1

            if op == "LOAD_CONST":
                v = f.code.consts[arg]
                if isinstance(v, CodeObject):
                    stack.append(Function(v))
                else:
                    stack.append(v)
            elif op == "LOAD_NAME":
                nm = f.code.names[arg]
                if nm not in self.globals:
                    raise NameError(f"undefined: {nm}")
                stack.append(self.globals[nm])
            elif op == "STORE_NAME":
                self.globals[f.code.names[arg]] = stack.pop()
            elif op == "LOAD_LOCAL":
                stack.append(f.locals[arg])
            elif op == "STORE_LOCAL":
                f.locals[arg] = stack.pop()
            elif op == "POP":
                stack.pop()
            elif op == "DUP":
                stack.append(stack[-1])
            elif op == "BIN_ADD":
                b = stack.pop(); a = stack.pop()
                if isinstance(a, str) or isinstance(b, str):
                    stack.append(_strify(a) + _strify(b))
                else:
                    stack.append(a + b)
            elif op == "BIN_SUB":
                b = stack.pop(); a = stack.pop(); stack.append(a - b)
            elif op == "BIN_MUL":
                b = stack.pop(); a = stack.pop(); stack.append(a * b)
            elif op == "BIN_DIV":
                b = stack.pop(); a = stack.pop()
                if isinstance(a, int) and isinstance(b, int) and b != 0:
                    stack.append(a // b if a % b == 0 else a / b)
                else:
                    stack.append(a / b)
            elif op == "BIN_MOD":
                b = stack.pop(); a = stack.pop(); stack.append(a % b)
            elif op == "CMP_EQ":
                b = stack.pop(); a = stack.pop(); stack.append(a == b)
            elif op == "CMP_NE":
                b = stack.pop(); a = stack.pop(); stack.append(a != b)
            elif op == "CMP_LT":
                b = stack.pop(); a = stack.pop(); stack.append(a < b)
            elif op == "CMP_LE":
                b = stack.pop(); a = stack.pop(); stack.append(a <= b)
            elif op == "CMP_GT":
                b = stack.pop(); a = stack.pop(); stack.append(a > b)
            elif op == "CMP_GE":
                b = stack.pop(); a = stack.pop(); stack.append(a >= b)
            elif op == "UNARY_NEG":
                stack.append(-stack.pop())
            elif op == "UNARY_NOT":
                stack.append(not _truthy(stack.pop()))
            elif op == "JUMP":
                f.pc = arg
            elif op == "JUMP_IF_FALSE":
                v = stack.pop()
                if not _truthy(v):
                    f.pc = arg
            elif op == "JUMP_IF_TRUE":
                v = stack.pop()
                if _truthy(v):
                    f.pc = arg
            elif op == "MAKE_LIST":
                items = stack[-arg:] if arg else []
                if arg:
                    del stack[-arg:]
                stack.append(items)
            elif op == "INDEX_GET":
                idx = stack.pop(); obj = stack.pop()
                stack.append(obj[int(idx)])
            elif op == "INDEX_SET":
                v = stack.pop(); idx = stack.pop(); obj = stack.pop()
                obj[int(idx)] = v
                stack.append(v)
            elif op == "PRINT":
                args = stack[-arg:] if arg else []
                if arg:
                    del stack[-arg:]
                print(*[_strify(a) for a in args])
            elif op == "BUILD_FUNC":
                v = f.code.consts[arg]
                stack.append(Function(v))
            elif op == "CALL":
                args = stack[-arg:] if arg else []
                if arg:
                    del stack[-arg:]
                func = stack.pop()
                if isinstance(func, BuiltinFn):
                    stack.append(func.fn(*args))
                elif isinstance(func, Function):
                    if len(args) != func.code.nparams:
                        raise TypeError(
                            f"{func.code.name} takes {func.code.nparams} args, got {len(args)}")
                    new_frame = Frame(
                        code=func.code, pc=0,
                        locals=list(args) + [None] * (func.code.nlocals - len(args)),
                    )
                    frames.append(new_frame)
                else:
                    raise TypeError(f"not callable: {func!r}")
            elif op == "RETURN":
                ret = stack.pop()
                frames.pop()
                stack.append(ret)
                if not frames:
                    return ret
            elif op == "HALT":
                return None
            else:
                raise RuntimeError(f"bad op {op}")
        return None


# ----------------------- helpers --------------------------------------------
@dataclass
class BuiltinFn:
    name: str
    fn: Any
    def __repr__(self): return f"<builtin {self.name}>"


def _builtin(n, f): return BuiltinFn(n, f)


def _truthy(v):
    if v is None or v is False or v == 0 or v == "":
        return False
    return True


def _strify(v) -> str:
    if v is None: return "nil"
    if v is True: return "true"
    if v is False: return "false"
    if isinstance(v, list): return "[" + ", ".join(_strify(x) for x in v) + "]"
    return str(v)


def _numify(v):
    if isinstance(v, (int, float)): return v
    try: return int(v)
    except (ValueError, TypeError):
        try: return float(v)
        except (ValueError, TypeError): return None


def _typeof(v):
    if v is None: return "nil"
    if isinstance(v, bool): return "bool"
    if isinstance(v, int): return "number"
    if isinstance(v, float): return "number"
    if isinstance(v, str): return "string"
    if isinstance(v, list): return "list"
    if isinstance(v, (Function, BuiltinFn)): return "function"
    return "?"


# ============================================================================
# 6. Disassembler
# ============================================================================
def disasm(co: CodeObject, indent: int = 0):
    pad = "  " * indent
    print(f"{pad}===== code <{co.name}> nparams={co.nparams} nlocals={co.nlocals} =====")
    print(f"{pad}consts: {[_const_repr(c) for c in co.consts]}")
    print(f"{pad}names : {co.names}")
    print(f"{pad}locals: {co.local_names}")
    for i, (op, arg) in enumerate(co.code):
        extra = ""
        if op in ("LOAD_CONST",) and isinstance(co.consts[arg], CodeObject):
            extra = f"   ; <code {co.consts[arg].name}>"
        elif op in ("LOAD_CONST",):
            extra = f"   ; {co.consts[arg]!r}"
        elif op in ("LOAD_NAME", "STORE_NAME"):
            extra = f"   ; {co.names[arg]}"
        elif op in ("LOAD_LOCAL", "STORE_LOCAL"):
            extra = f"   ; {co.local_names[arg]}"
        elif op in ("BUILD_FUNC",):
            extra = f"   ; <code {co.consts[arg].name}>"
        print(f"{pad}{i:4d}  {op:<14} {arg}{extra}")
    for c in co.consts:
        if isinstance(c, CodeObject):
            disasm(c, indent + 1)


def _const_repr(c):
    if isinstance(c, CodeObject):
        return f"<code {c.name}>"
    return repr(c)


# ============================================================================
# 7. CLI / demo
# ============================================================================
DEMO_SRC = r"""
// PyVM demo: 算术 / 控制流 / 函数 / 递归 / 列表

let g = 100;

fn add(a, b) {
    return a + b;
}

fn fact(n) {
    if (n <= 1) { return 1; }
    return n * fact(n - 1);
}

fn fib(n) {
    if (n < 2) { return n; }
    return fib(n-1) + fib(n-2);
}

fn sum_list(xs) {
    let s = 0;
    for (let i = 0; i < len(xs); i = i + 1) {
        s = s + xs[i];
    }
    return s;
}

print("g =", g);
print("add(2, 3) =", add(2, 3));
print("10! =", fact(10));
print("fib(15) =", fib(15));
print("sum([1..5]) =", sum_list([1, 2, 3, 4, 5]));

// loop
let i = 0;
let acc = 0;
while (i < 10) {
    acc = acc + i;
    i = i + 1;
}
print("0+1+...+9 =", acc);

// nested call
print("fact(add(3,2)) =", fact(add(3, 2)));
"""


def compile_source(src: str) -> CodeObject:
    toks = tokenize(src)
    ast = Parser(toks).parse()
    return Compiler("<main>").compile_program(ast)


def main():
    args = sys.argv[1:]
    if not args or args[0] == "demo":
        print("=== source ===")
        print(DEMO_SRC.strip())
        print("\n=== compile + disasm ===")
        co = compile_source(DEMO_SRC)
        disasm(co)
        print("\n=== run ===")
        VM().run(co)
        return
    if args[0] == "asm" and len(args) >= 2:
        src = open(args[1], encoding="utf-8").read()
        disasm(compile_source(src))
        return
    if args[0] == "run" and len(args) >= 2:
        src = open(args[1], encoding="utf-8").read()
        VM().run(compile_source(src))
        return
    if args[0] == "vm" and len(args) >= 2:
        d = json.loads(open(args[1], encoding="utf-8").read())
        VM().run(CodeObject.from_json(d))
        return
    if args[0] == "save" and len(args) >= 3:
        src = open(args[1], encoding="utf-8").read()
        co = compile_source(src)
        open(args[2], "w", encoding="utf-8").write(json.dumps(co.to_json(), indent=2))
        print(f"saved bytecode -> {args[2]}")
        return
    print("usage: pyvm.py demo | asm <src> | run <src> | save <src> <out.json> | vm <out.json>")


if __name__ == "__main__":
    main()
