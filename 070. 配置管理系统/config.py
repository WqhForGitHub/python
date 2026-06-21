# -*- coding: utf-8 -*-
"""
配置管理系统
- 纯 Python 实现，不依赖第三方库
- 支持加载 .json / .ini / .env / 简易 .yml（缩进式 key: value）
- 多源合并：默认值 < 文件 < 环境变量 < 命令行覆盖
- 路径访问：cfg.get("db.host") / cfg["db.host"] / cfg.set("db.port", 5432)
- 类型转换：as_int / as_bool / as_list
- 变量插值：${other.key}
- 监听变更回调
- 保存为 JSON

用法：
    python config.py
"""
import json
import os
import re
import sys
from pathlib import Path


# ---------- 解析器 ----------
def parse_json(text):
    return json.loads(text)


def parse_ini(text):
    """简易 INI: [section] / key = value, 支持 ; # 注释"""
    out = {}
    section = "default"
    out[section] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            out.setdefault(section, {})
        elif "=" in line:
            k, v = line.split("=", 1)
            out[section][k.strip()] = v.strip()
    if not out["default"]:
        out.pop("default")
    return out


def parse_env(text):
    """KEY=VALUE 一行一对"""
    out = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            v = v.strip().strip('"').strip("'")
            out[k.strip()] = v
    return out


def parse_yaml(text):
    """极简缩进式 YAML：仅支持 'key: value' 与嵌套字典，不支持列表/锚点"""
    lines = [l for l in text.splitlines() if l.strip() and not l.lstrip().startswith("#")]

    def parse_block(start_idx, indent):
        result = {}
        i = start_idx
        while i < len(lines):
            line = lines[i]
            cur_indent = len(line) - len(line.lstrip())
            if cur_indent < indent:
                return result, i
            if cur_indent > indent:
                i += 1; continue
            stripped = line.strip()
            if ":" not in stripped:
                i += 1; continue
            k, _, v = stripped.partition(":")
            k = k.strip(); v = v.strip()
            if v == "":
                # 嵌套
                child, i = parse_block(i + 1, indent + 2)
                result[k] = child
            else:
                # 简单值
                if v.lower() == "true": v = True
                elif v.lower() == "false": v = False
                elif v.lower() in ("null", "~"): v = None
                else:
                    try: v = int(v)
                    except ValueError:
                        try: v = float(v)
                        except ValueError:
                            v = v.strip('"').strip("'")
                result[k] = v
                i += 1
        return result, i

    data, _ = parse_block(0, 0)
    return data


PARSERS = {
    ".json": parse_json,
    ".ini": parse_ini,
    ".cfg": parse_ini,
    ".env": parse_env,
    ".yml": parse_yaml,
    ".yaml": parse_yaml,
}


# ---------- 配置容器 ----------
class Config:
    _SEP = "."

    def __init__(self, defaults=None):
        self._data = dict(defaults or {})
        self._listeners = []

    # ---- 加载 ----
    def load_file(self, path):
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(path)
        ext = path.suffix.lower()
        parser = PARSERS.get(ext)
        if parser is None:
            raise ValueError(f"不支持的格式: {ext}")
        text = path.read_text(encoding="utf-8")
        data = parser(text)
        self._merge(self._data, data)
        return self

    def load_env(self, prefix=""):
        """按前缀加载环境变量（如 APP_DB_HOST -> db.host）"""
        for k, v in os.environ.items():
            if prefix and not k.startswith(prefix):
                continue
            key = k[len(prefix):] if prefix else k
            key = key.lower().replace("_", ".")
            self.set(key, v)
        return self

    def load_argv(self, argv=None):
        """支持 --foo.bar=baz 形式"""
        argv = argv if argv is not None else sys.argv[1:]
        for a in argv:
            if a.startswith("--") and "=" in a:
                k, v = a[2:].split("=", 1)
                self.set(k, v)
        return self

    @staticmethod
    def _merge(base, new):
        for k, v in new.items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                Config._merge(base[k], v)
            else:
                base[k] = v

    # ---- 访问 ----
    def get(self, key, default=None):
        node = self._data
        for part in key.split(self._SEP):
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                return default
        return self._interpolate(node)

    def set(self, key, value):
        old = self.get(key)
        node = self._data
        parts = key.split(self._SEP)
        for p in parts[:-1]:
            if p not in node or not isinstance(node[p], dict):
                node[p] = {}
            node = node[p]
        node[parts[-1]] = value
        if old != value:
            for cb in self._listeners:
                try: cb(key, old, value)
                except Exception: pass

    def __getitem__(self, key): return self.get(key)
    def __setitem__(self, key, value): self.set(key, value)
    def __contains__(self, key): return self.get(key) is not None

    # ---- 类型 ----
    def as_int(self, key, default=0):
        v = self.get(key, default)
        try: return int(v)
        except (TypeError, ValueError): return default

    def as_bool(self, key, default=False):
        v = self.get(key, default)
        if isinstance(v, bool): return v
        if isinstance(v, str): return v.lower() in ("1", "true", "yes", "on")
        return bool(v)

    def as_list(self, key, sep=",", default=None):
        v = self.get(key)
        if v is None: return list(default or [])
        if isinstance(v, list): return v
        return [s.strip() for s in str(v).split(sep) if s.strip()]

    # ---- 插值 ----
    _INTERP = re.compile(r"\$\{([^}]+)\}")

    def _interpolate(self, value):
        if not isinstance(value, str): return value
        def repl(m):
            ref = self.get(m.group(1))
            return str(ref) if ref is not None else m.group(0)
        return self._INTERP.sub(repl, value)

    # ---- 监听 ----
    def on_change(self, callback):
        self._listeners.append(callback)

    # ---- 输出 ----
    def to_dict(self):
        return dict(self._data)

    def save(self, path):
        Path(path).write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def __repr__(self):
        return f"Config({self._data})"


# ---------- demo ----------
def demo():
    base_dir = Path(__file__).parent
    # 写示例配置
    (base_dir / "config.json").write_text(json.dumps({
        "app": {"name": "PyConf", "debug": False},
        "db": {"host": "localhost", "port": 5432},
        "greeting": "Hello, ${app.name}!"
    }, indent=2), encoding="utf-8")

    (base_dir / "extra.ini").write_text(
        "[db]\nhost = override.local\nuser = admin\n", encoding="utf-8"
    )

    cfg = Config(defaults={"app": {"name": "default", "debug": True}})
    cfg.load_file(base_dir / "config.json")
    cfg.load_file(base_dir / "extra.ini")

    # 命令行覆盖
    cfg.load_argv(["--db.port=6543", "--app.debug=true"])

    cfg.on_change(lambda k, o, n: print(f"[变更] {k}: {o} -> {n}"))

    print("app.name        :", cfg.get("app.name"))
    print("app.debug (bool):", cfg.as_bool("app.debug"))
    print("db.host         :", cfg.get("db.host"))
    print("db.port (int)   :", cfg.as_int("db.port"))
    print("db.user         :", cfg["db.user"])
    print("greeting (插值) :", cfg.get("greeting"))

    # 修改并保存
    cfg.set("db.port", 9999)
    cfg.save(base_dir / "merged.json")
    print("已保存 merged.json")


if __name__ == "__main__":
    demo()
