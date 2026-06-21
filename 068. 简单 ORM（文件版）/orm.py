# -*- coding: utf-8 -*-
"""
简单 ORM（文件版）
- 数据存储：每张表一个 JSON 文件，存放在 db_dir 目录下
- 字段类型：IntegerField / StringField / FloatField / BooleanField / DateField
- 模型：继承 Model 即生成表，支持
       create / save / delete / get / filter / all / count / order_by
- 主键自增
- 简易查询过滤：lt / lte / gt / gte / eq / in / contains / startswith
- 事务（手动 begin/commit/rollback）

用法：
    python orm.py        # 运行内置 demo
"""
import json
import os
import shutil
import threading
from copy import deepcopy
from datetime import date, datetime
from pathlib import Path


# ---------- 字段 ----------
class Field:
    py_type = object

    def __init__(self, default=None, primary_key=False, nullable=True):
        self.default = default
        self.primary_key = primary_key
        self.nullable = nullable
        self.name = None  # 由 Model 元类设置

    def to_python(self, value):
        if value is None:
            return None
        return self.py_type(value)

    def to_storage(self, value):
        return value

    def validate(self, value):
        if value is None and not self.nullable and not self.primary_key:
            raise ValueError(f"字段 {self.name} 不可为空")


class IntegerField(Field):
    py_type = int


class FloatField(Field):
    py_type = float


class StringField(Field):
    py_type = str

    def __init__(self, max_length=None, **kw):
        super().__init__(**kw)
        self.max_length = max_length

    def validate(self, value):
        super().validate(value)
        if value is not None and self.max_length and len(value) > self.max_length:
            raise ValueError(f"字段 {self.name} 超出最大长度 {self.max_length}")


class BooleanField(Field):
    py_type = bool


class DateField(Field):
    py_type = date

    def to_python(self, value):
        if value is None: return None
        if isinstance(value, date): return value
        return datetime.strptime(value, "%Y-%m-%d").date()

    def to_storage(self, value):
        if value is None: return None
        if isinstance(value, date): return value.isoformat()
        return value


# ---------- 数据库后端 ----------
class Database:
    def __init__(self, db_dir="data"):
        self.db_dir = Path(db_dir)
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._tx = None  # 事务快照 {table: rows_copy}

    def _table_path(self, table):
        return self.db_dir / f"{table}.json"

    def load(self, table):
        path = self._table_path(table)
        if not path.exists():
            return {"auto_id": 0, "rows": []}
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, table, data):
        path = self._table_path(table)
        tmp = path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)

    # 事务
    def begin(self):
        with self._lock:
            self._tx = {}

    def snapshot(self, table):
        if self._tx is not None and table not in self._tx:
            self._tx[table] = deepcopy(self.load(table))

    def commit(self):
        with self._lock:
            self._tx = None

    def rollback(self):
        with self._lock:
            if self._tx is None: return
            for table, snap in self._tx.items():
                self.save(table, snap)
            self._tx = None


_default_db = Database()


# ---------- 元类 / 模型 ----------
class ModelMeta(type):
    def __new__(mcs, name, bases, ns):
        if name == "Model":
            return super().__new__(mcs, name, bases, ns)

        fields = {}
        pk = None
        for k, v in list(ns.items()):
            if isinstance(v, Field):
                v.name = k
                fields[k] = v
                if v.primary_key:
                    pk = k

        if pk is None:
            # 自动添加 id 主键
            pk_field = IntegerField(primary_key=True)
            pk_field.name = "id"
            fields["id"] = pk_field
            pk = "id"

        ns["_fields"] = fields
        ns["_pk"] = pk
        ns["_table"] = ns.get("_table", name.lower())
        return super().__new__(mcs, name, bases, ns)


class Model(metaclass=ModelMeta):
    _db = _default_db

    def __init__(self, **kwargs):
        for name, field in self._fields.items():
            value = kwargs.get(name, field.default)
            setattr(self, name, value)

    # ---- 序列化 ----
    def to_dict(self):
        out = {}
        for name, field in self._fields.items():
            out[name] = field.to_storage(getattr(self, name, None))
        return out

    @classmethod
    def from_dict(cls, d):
        obj = cls()
        for name, field in cls._fields.items():
            setattr(obj, name, field.to_python(d.get(name)))
        return obj

    # ---- CRUD ----
    @classmethod
    def _read(cls):
        cls._db.snapshot(cls._table)
        return cls._db.load(cls._table)

    @classmethod
    def _write(cls, data):
        cls._db.save(cls._table, data)

    def save(self):
        for name, field in self._fields.items():
            field.validate(getattr(self, name, None))
        data = self._read()
        pk = self._pk
        pk_val = getattr(self, pk, None)

        if pk_val is None:
            data["auto_id"] += 1
            setattr(self, pk, data["auto_id"])
            data["rows"].append(self.to_dict())
        else:
            replaced = False
            for i, row in enumerate(data["rows"]):
                if row.get(pk) == pk_val:
                    data["rows"][i] = self.to_dict()
                    replaced = True; break
            if not replaced:
                data["rows"].append(self.to_dict())

        self._write(data)
        return self

    def delete(self):
        data = self._read()
        pk = self._pk; pk_val = getattr(self, pk, None)
        data["rows"] = [r for r in data["rows"] if r.get(pk) != pk_val]
        self._write(data)

    @classmethod
    def create(cls, **kwargs):
        return cls(**kwargs).save()

    @classmethod
    def all(cls):
        data = cls._read()
        return [cls.from_dict(r) for r in data["rows"]]

    @classmethod
    def get(cls, **kwargs):
        results = cls.filter(**kwargs)
        if not results:
            raise LookupError(f"{cls.__name__} 未找到 {kwargs}")
        if len(results) > 1:
            raise LookupError(f"{cls.__name__} 多条匹配 {kwargs}")
        return results[0]

    @classmethod
    def filter(cls, **kwargs):
        rows = cls.all()
        return [r for r in rows if cls._match(r, kwargs)]

    @classmethod
    def count(cls, **kwargs):
        return len(cls.filter(**kwargs)) if kwargs else len(cls.all())

    @classmethod
    def order_by(cls, key, reverse=False):
        return sorted(cls.all(), key=lambda r: getattr(r, key), reverse=reverse)

    # ---- 过滤器 ----
    @staticmethod
    def _match(obj, conditions):
        for key, expected in conditions.items():
            if "__" in key:
                field, op = key.split("__", 1)
            else:
                field, op = key, "eq"
            actual = getattr(obj, field, None)
            if op == "eq" and actual != expected: return False
            elif op == "lt" and not (actual is not None and actual < expected): return False
            elif op == "lte" and not (actual is not None and actual <= expected): return False
            elif op == "gt" and not (actual is not None and actual > expected): return False
            elif op == "gte" and not (actual is not None and actual >= expected): return False
            elif op == "in" and actual not in expected: return False
            elif op == "contains" and (actual is None or expected not in actual): return False
            elif op == "startswith" and (actual is None or not str(actual).startswith(expected)):
                return False
        return True

    def __repr__(self):
        kv = ", ".join(f"{k}={getattr(self, k)!r}" for k in self._fields)
        return f"{self.__class__.__name__}({kv})"


# ---------- demo ----------
class User(Model):
    _table = "users"
    name = StringField(max_length=32, nullable=False)
    age = IntegerField(default=0)
    email = StringField()


class Post(Model):
    _table = "posts"
    title = StringField(nullable=False)
    body = StringField()
    user_id = IntegerField()
    created = DateField()


def demo():
    # 清空旧数据
    if Path("data").exists():
        shutil.rmtree("data")
    User._db = Database("data")
    Post._db = Database("data")

    # 创建
    alice = User.create(name="Alice", age=30, email="a@x.com")
    bob = User.create(name="Bob", age=25, email="b@x.com")
    User.create(name="Carol", age=40)
    print("所有用户:", User.all())

    # 查询
    print("年龄>=30:", User.filter(age__gte=30))
    print("名字包含 'o':", User.filter(name__contains="o"))
    print("第一个 Alice:", User.get(name="Alice"))

    # 更新
    alice.age = 31
    alice.save()
    print("Alice 更新后:", User.get(name="Alice"))

    # 关联
    Post.create(title="Hello", body="first", user_id=alice.id, created=date.today())
    Post.create(title="World", body="second", user_id=bob.id, created=date.today())
    print("Alice 的帖子:", Post.filter(user_id=alice.id))

    # 排序 / 计数
    print("按年龄倒序:", User.order_by("age", reverse=True))
    print("用户总数:", User.count())

    # 删除
    bob.delete()
    print("删除 Bob 后:", User.all())

    # 事务
    db = User._db
    db.begin()
    User.create(name="TempUser", age=99)
    print("事务中:", User.count())
    db.rollback()
    print("回滚后:", User.count())


if __name__ == "__main__":
    demo()
