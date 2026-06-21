"""
自动代码生成器 - 纯 Python 实现
=====================================
功能：
1. 模板引擎（自实现，类 Jinja2 子集）：变量 {{ var }}, 控制 {% for %}, {% if %}
2. 从 JSON Schema 生成 Python dataclass / SQL 建表 / REST 路由
3. CLI 子命令：dataclass / sql / api
"""

import json
import re
import sys


# ---------- 极简模板引擎 ----------
class Template:
    """支持 {{ expr }}，{% for x in xs %} ... {% endfor %}，{% if cond %} ... {% endif %}"""

    TOKEN_RE = re.compile(r"({{.*?}}|{%.*?%})", re.DOTALL)

    def __init__(self, source):
        self.source = source

    def render(self, ctx):
        tokens = self.TOKEN_RE.split(self.source)
        return self._render_block(tokens, 0, ctx)[0]

    def _render_block(self, tokens, i, ctx, end_tags=()):
        out = []
        while i < len(tokens):
            tok = tokens[i]
            if tok.startswith("{{") and tok.endswith("}}"):
                expr = tok[2:-2].strip()
                out.append(str(self._eval(expr, ctx)))
                i += 1
            elif tok.startswith("{%") and tok.endswith("%}"):
                stmt = tok[2:-2].strip()
                if stmt.split()[0] in end_tags:
                    return "".join(out), i
                if stmt.startswith("for "):
                    m = re.match(r"for\s+(\w+)\s+in\s+(.+)", stmt)
                    var = m.group(1)
                    iterable = self._eval(m.group(2), ctx)
                    body_start = i + 1
                    # 找到对应 endfor
                    body_text, end_i = self._render_block(tokens, body_start, ctx, ("endfor",))
                    # 上面 body_text 是按 ctx 渲染了一次的内容，无法循环；改为收集 raw tokens
                    # 重新实现：先扫描出 body tokens
                    pass  # 用下面新逻辑
                    # —— 重新设计 ——
                    body_tokens, end_i = self._extract_block(tokens, body_start, "endfor")
                    inner = []
                    for item in iterable:
                        new_ctx = dict(ctx, **{var: item})
                        rendered, _ = self._render_block(body_tokens, 0, new_ctx)
                        inner.append(rendered)
                    out.append("".join(inner))
                    i = end_i + 1
                elif stmt.startswith("if "):
                    cond = stmt[3:].strip()
                    body_start = i + 1
                    body_tokens, end_i = self._extract_block(tokens, body_start, "endif")
                    if self._eval(cond, ctx):
                        rendered, _ = self._render_block(body_tokens, 0, ctx)
                        out.append(rendered)
                    i = end_i + 1
                else:
                    i += 1  # 忽略未知
            else:
                out.append(tok)
                i += 1
        return "".join(out), i

    def _extract_block(self, tokens, start, end_tag):
        """从 start 开始截取直到匹配的 end_tag（处理嵌套）"""
        depth = 1
        i = start
        out = []
        while i < len(tokens):
            tok = tokens[i]
            if tok.startswith("{%") and tok.endswith("%}"):
                stmt = tok[2:-2].strip()
                kw = stmt.split()[0]
                if kw in ("for", "if"):
                    depth += 1
                elif kw == end_tag:
                    depth -= 1
                    if depth == 0:
                        return out, i
            out.append(tok)
            i += 1
        return out, i

    def _eval(self, expr, ctx):
        try:
            return eval(expr, {"__builtins__": {}}, ctx)
        except Exception as e:
            return f"<ERR: {e}>"


# ---------- 代码生成器 ----------
PY_TYPE_MAP = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "array": "list",
    "object": "dict",
}

SQL_TYPE_MAP = {
    "string": "VARCHAR(255)",
    "integer": "INTEGER",
    "number": "REAL",
    "boolean": "BOOLEAN",
}


DATACLASS_TPL = """from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class {{ name }}:
{% for f in fields %}    {{ f['name'] }}: {{ f['type'] }}{% if f['default'] %} = {{ f['default'] }}{% endif %}
{% endfor %}
"""


SQL_TPL = """CREATE TABLE {{ name|lower }} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
{% for f in fields %}    {{ f['name'] }} {{ f['sql_type'] }}{% if f['nullable'] %}{% else %} NOT NULL{% endif %}{% if not f['last'] %},{% endif %}
{% endfor %});
"""


API_TPL = """# Auto-generated REST API stub for {{ name }}
from http.server import BaseHTTPRequestHandler
import json

ROUTES = {
{% for r in routes %}    "{{ r['method'] }} {{ r['path'] }}": "{{ r['handler'] }}",
{% endfor %}}


class {{ name }}Handler(BaseHTTPRequestHandler):
{% for r in routes %}    def {{ r['handler'] }}(self):
        # TODO: implement {{ r['method'] }} {{ r['path'] }}
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode())

{% endfor %}"""


def gen_dataclass(schema):
    name = schema["name"]
    fields = []
    for f in schema["fields"]:
        py_type = PY_TYPE_MAP.get(f["type"], "Any")
        if f.get("optional"):
            py_type = f"Optional[{py_type}]"
        default = f.get("default")
        if default is not None:
            default = repr(default)
        elif f.get("optional"):
            default = "None"
        fields.append({"name": f["name"], "type": py_type, "default": default})
    return Template(DATACLASS_TPL).render({"name": name, "fields": fields})


def gen_sql(schema):
    fields = []
    for f in schema["fields"]:
        sql_type = SQL_TYPE_MAP.get(f["type"], "TEXT")
        fields.append({
            "name": f["name"],
            "sql_type": sql_type,
            "nullable": f.get("optional", False),
            "last": False,
        })
    if fields:
        fields[-1]["last"] = True
    # 简单处理 |lower 过滤器
    src = SQL_TPL.replace("{{ name|lower }}", schema["name"].lower())
    return Template(src).render({"fields": fields})


def gen_api(schema):
    name = schema["name"]
    res = name.lower() + "s"
    routes = [
        {"method": "GET",    "path": f"/{res}",      "handler": f"list_{res}"},
        {"method": "POST",   "path": f"/{res}",      "handler": f"create_{res}"},
        {"method": "GET",    "path": f"/{res}/<id>", "handler": f"get_{res}"},
        {"method": "PUT",    "path": f"/{res}/<id>", "handler": f"update_{res}"},
        {"method": "DELETE", "path": f"/{res}/<id>", "handler": f"delete_{res}"},
    ]
    return Template(API_TPL).render({"name": name, "routes": routes})


# ---------- CLI ----------
DEMO_SCHEMA = {
    "name": "User",
    "fields": [
        {"name": "id", "type": "integer"},
        {"name": "username", "type": "string"},
        {"name": "email", "type": "string", "optional": True},
        {"name": "age", "type": "integer", "default": 0},
        {"name": "active", "type": "boolean", "default": True},
    ],
}


def main():
    args = sys.argv[1:]
    if not args:
        # 演示模式
        demo()
        return

    cmd = args[0]
    schema_path = args[1] if len(args) > 1 else None
    schema = json.load(open(schema_path)) if schema_path else DEMO_SCHEMA
    if cmd == "dataclass":
        print(gen_dataclass(schema))
    elif cmd == "sql":
        print(gen_sql(schema))
    elif cmd == "api":
        print(gen_api(schema))
    else:
        print("用法: python codegen.py [dataclass|sql|api] [schema.json]")


def demo():
    print("=" * 60)
    print("【自动代码生成器】Demo Schema:", DEMO_SCHEMA["name"])
    print("=" * 60)
    print("\n--- Python @dataclass ---")
    print(gen_dataclass(DEMO_SCHEMA))
    print("--- SQL CREATE TABLE ---")
    print(gen_sql(DEMO_SCHEMA))
    print("--- REST API Stub ---")
    print(gen_api(DEMO_SCHEMA))


if __name__ == "__main__":
    main()
