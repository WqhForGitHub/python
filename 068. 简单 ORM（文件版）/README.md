# 简单 ORM（文件版）

纯 Python 实现的极简 ORM，每张表对应一个 JSON 文件。

## 特性
- 字段类型：`IntegerField`, `StringField`, `FloatField`, `BooleanField`, `DateField`
- 自增主键（默认 `id`）
- CRUD：`create / save / delete / get / filter / all / count / order_by`
- 查询过滤后缀：`__eq / __lt / __lte / __gt / __gte / __in / __contains / __startswith`
- 简易事务：`db.begin() / db.commit() / db.rollback()`

## 用法
```python
from orm import Model, StringField, IntegerField

class User(Model):
    name = StringField(max_length=32, nullable=False)
    age = IntegerField(default=0)

User.create(name="Alice", age=30)
print(User.filter(age__gte=18))
```

运行 demo：
```bash
python orm.py
```
