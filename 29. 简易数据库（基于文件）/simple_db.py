"""
简易数据库（基于文件）
功能：实现一个基于文件的简易关系型数据库，支持建表、插入、查询、更新、删除、
      索引、事务、表连接等操作，数据持久化到文件
"""

import json
import os
import time
import shutil
from datetime import datetime


class SimpleDB:
    """简易文件数据库"""

    def __init__(self, db_name: str = "mydb", db_dir: str = None):
        self.db_name = db_name
        self.db_dir = db_dir or os.path.join(
            os.path.dirname(__file__), f".db_{db_name}"
        )
        self.tables = {}  # 表名 -> Table 对象
        self._in_transaction = False
        self._transaction_backup = None

        os.makedirs(self.db_dir, exist_ok=True)
        self._load_all()

    # ==================== 数据库管理 ====================

    def _load_all(self):
        """加载所有表"""
        meta_path = os.path.join(self.db_dir, "_meta.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            for table_name in meta.get("tables", []):
                self.tables[table_name] = Table(table_name, self.db_dir)
                self.tables[table_name]._load()

    def _save_meta(self):
        """保存数据库元数据"""
        meta_path = os.path.join(self.db_dir, "_meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(
                {"tables": list(self.tables.keys())}, f, ensure_ascii=False, indent=2
            )

    def create_table(self, name: str, columns: dict, primary_key: str = None):
        """建表
        columns: {列名: 类型}，类型支持 int, float, str, bool
        primary_key: 主键列名
        """
        if name in self.tables:
            raise ValueError(f"表 '{name}' 已存在")
        table = Table(name, self.db_dir, columns, primary_key)
        self.tables[name] = table
        self._save_meta()
        print(f"表 '{name}' 创建成功，列: {columns}，主键: {primary_key}")

    def drop_table(self, name: str):
        """删除表"""
        if name not in self.tables:
            raise ValueError(f"表 '{name}' 不存在")
        self.tables[name]._drop()
        del self.tables[name]
        self._save_meta()
        print(f"表 '{name}' 已删除")

    def table(self, name: str) -> "Table":
        """获取表对象"""
        if name not in self.tables:
            raise ValueError(f"表 '{name}' 不存在")
        return self.tables[name]

    def show_tables(self):
        """显示所有表"""
        print(f"\n数据库 '{self.db_name}' 中的表:")
        for name, table in self.tables.items():
            print(f"  {name}: {len(table.rows)} 行, 列: {table.columns}")

    # ==================== 事务 ====================

    def begin(self):
        """开始事务"""
        if self._in_transaction:
            raise RuntimeError("已在事务中")
        self._in_transaction = True
        self._transaction_backup = self.db_dir + "_backup"
        if os.path.exists(self._transaction_backup):
            shutil.rmtree(self._transaction_backup)
        shutil.copytree(self.db_dir, self._transaction_backup)
        print("事务开始")

    def commit(self):
        """提交事务"""
        if not self._in_transaction:
            raise RuntimeError("不在事务中")
        if os.path.exists(self._transaction_backup):
            shutil.rmtree(self._transaction_backup)
        self._in_transaction = False
        self._transaction_backup = None
        print("事务已提交")

    def rollback(self):
        """回滚事务"""
        if not self._in_transaction:
            raise RuntimeError("不在事务中")
        # 恢复备份
        shutil.rmtree(self.db_dir)
        shutil.copytree(self._transaction_backup, self.db_dir)
        shutil.rmtree(self._transaction_backup)
        self._in_transaction = False
        self._transaction_backup = None
        self.tables = {}
        self._load_all()
        print("事务已回滚")

    # ==================== 表连接 ====================

    def join(
        self, table1_name: str, table2_name: str, on: tuple, join_type: str = "inner"
    ) -> list:
        """表连接
        on: (表1列名, 表2列名)
        join_type: inner, left, right
        """
        t1 = self.tables[table1_name]
        t2 = self.tables[table2_name]
        col1, col2 = on

        results = []
        for r1 in t1.rows:
            matched = False
            for r2 in t2.rows:
                if r1.get(col1) == r2.get(col2):
                    row = {}
                    for k, v in r1.items():
                        row[f"{table1_name}.{k}"] = v
                    for k, v in r2.items():
                        if k != col2:
                            row[f"{table2_name}.{k}"] = v
                    results.append(row)
                    matched = True

            if not matched and join_type == "left":
                row = {}
                for k, v in r1.items():
                    row[f"{table1_name}.{k}"] = v
                for k in t2.columns:
                    if k != col2:
                        row[f"{table2_name}.{k}"] = None
                results.append(row)

        if join_type == "right":
            for r2 in t2.rows:
                matched = any(r1.get(col1) == r2.get(col2) for r1 in t1.rows)
                if not matched:
                    row = {}
                    for k in t1.columns:
                        row[f"{table1_name}.{k}"] = None
                    for k, v in r2.items():
                        if k != col2:
                            row[f"{table2_name}.{k}"] = v
                    results.append(row)

        return results

    def close(self):
        """关闭数据库"""
        if self._in_transaction:
            self.rollback()
        print(f"数据库 '{self.db_name}' 已关闭")


class Table:
    """数据库表"""

    TYPE_MAP = {
        "int": int,
        "float": float,
        "str": str,
        "bool": bool,
    }

    def __init__(
        self, name: str, db_dir: str, columns: dict = None, primary_key: str = None
    ):
        self.name = name
        self.db_dir = db_dir
        self.columns = columns or {}
        self.primary_key = primary_key
        self.rows = []
        self.indexes = {}  # 列名 -> {值: [行索引]}
        self._next_id = 1
        self._filepath = os.path.join(db_dir, f"{name}.json")

        if columns:
            self._save()

    # ==================== 持久化 ====================

    def _load(self):
        """从文件加载"""
        if os.path.exists(self._filepath):
            with open(self._filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.columns = data.get("columns", {})
            self.primary_key = data.get("primary_key")
            self.rows = data.get("rows", [])
            self._next_id = data.get("next_id", 1)
            # 重建索引
            for col in self.indexes:
                self._build_index(col)

    def _save(self):
        """保存到文件"""
        data = {
            "columns": self.columns,
            "primary_key": self.primary_key,
            "rows": self.rows,
            "next_id": self._next_id,
        }
        with open(self._filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _drop(self):
        """删除表文件"""
        if os.path.exists(self._filepath):
            os.remove(self._filepath)

    # ==================== 类型检查 ====================

    def _cast_value(self, column: str, value):
        """转换值的类型"""
        if column not in self.columns:
            raise ValueError(f"列 '{column}' 不存在")
        col_type = self.columns[column]
        if value is None:
            return None
        try:
            if col_type == "int":
                return int(value)
            elif col_type == "float":
                return float(value)
            elif col_type == "str":
                return str(value)
            elif col_type == "bool":
                if isinstance(value, str):
                    return value.lower() in ("true", "1", "yes")
                return bool(value)
        except (ValueError, TypeError):
            raise ValueError(f"列 '{column}' 期望类型 {col_type}，得到: {value!r}")

    # ==================== CRUD ====================

    def insert(self, record: dict) -> int:
        """插入一条记录"""
        row = {"_id": self._next_id}

        for col, col_type in self.columns.items():
            if col in record:
                row[col] = self._cast_value(col, record[col])
            elif col == self.primary_key:
                raise ValueError(f"主键 '{col}' 不能为空")
            else:
                row[col] = None

        # 主键唯一性检查
        if self.primary_key:
            pk_value = row[self.primary_key]
            for existing in self.rows:
                if existing.get(self.primary_key) == pk_value:
                    raise ValueError(f"主键冲突: {self.primary_key}={pk_value}")

        row["_created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.rows.append(row)
        self._next_id += 1
        self._save()
        return row["_id"]

    def insert_many(self, records: list) -> list:
        """批量插入"""
        ids = []
        for r in records:
            ids.append(self.insert(r))
        return ids

    def select(
        self,
        where: callable = None,
        columns: list = None,
        order_by: str = None,
        limit: int = None,
        offset: int = 0,
    ) -> list:
        """查询记录"""
        results = self.rows
        if where:
            results = [r for r in results if where(r)]
        if order_by:
            desc = order_by.startswith("-")
            col = order_by.lstrip("-")
            results = sorted(results, key=lambda r: r.get(col, ""), reverse=desc)
        results = results[offset:]
        if limit:
            results = results[:limit]
        if columns:
            results = [{c: r.get(c) for c in columns} for r in results]
        return results

    def update(self, where: callable, updates: dict) -> int:
        """更新记录，返回更新数量"""
        count = 0
        for r in self.rows:
            if where(r):
                for col, value in updates.items():
                    if col in self.columns:
                        r[col] = self._cast_value(col, value)
                r["_updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                count += 1
        if count:
            self._save()
        return count

    def delete(self, where: callable) -> int:
        """删除记录，返回删除数量"""
        before = len(self.rows)
        self.rows = [r for r in self.rows if not where(r)]
        count = before - len(self.rows)
        if count:
            self._save()
        return count

    # ==================== 索引 ====================

    def create_index(self, column: str):
        """创建索引"""
        if column not in self.columns:
            raise ValueError(f"列 '{column}' 不存在")
        self.indexes[column] = {}
        self._build_index(column)
        print(f"索引 '{column}' 创建成功")

    def _build_index(self, column: str):
        """构建索引"""
        self.indexes[column] = {}
        for i, row in enumerate(self.rows):
            value = row.get(column)
            if value is not None:
                if value not in self.indexes[column]:
                    self.indexes[column][value] = []
                self.indexes[column][value].append(i)

    def find_by_index(self, column: str, value) -> list:
        """通过索引查找"""
        if column not in self.indexes:
            return self.select(where=lambda r: r.get(column) == value)
        indices = self.indexes[column].get(value, [])
        return [self.rows[i] for i in indices]

    # ==================== 统计 ====================

    def count(self, where: callable = None) -> int:
        """记录数"""
        if where:
            return sum(1 for r in self.rows if where(r))
        return len(self.rows)

    def aggregate(self, column: str, func: str) -> float | None:
        """聚合: sum, avg, min, max"""
        values = [
            r[column]
            for r in self.rows
            if column in r and isinstance(r[column], (int, float))
        ]
        if not values:
            return None
        if func == "sum":
            return sum(values)
        elif func == "avg":
            return sum(values) / len(values)
        elif func == "min":
            return min(values)
        elif func == "max":
            return max(values)

    def display(self, rows: list = None):
        """表格形式显示"""
        data = rows or self.rows
        if not data:
            print("  (空表)")
            return

        cols = ["_id"] + list(self.columns.keys())
        col_widths = {}
        for col in cols:
            max_len = max(len(str(col)), *(len(str(r.get(col, ""))) for r in data))
            col_widths[col] = min(max_len, 20)

        header = " | ".join(str(col).ljust(col_widths[col]) for col in cols)
        sep = "-+-".join("-" * col_widths[col] for col in cols)
        print(f"  表: {self.name}")
        print(f"  {header}")
        print(f"  {sep}")
        for r in data[:30]:
            row_str = " | ".join(
                str(r.get(col, ""))[:20].ljust(col_widths[col]) for col in cols
            )
            print(f"  {row_str}")


if __name__ == "__main__":
    # ===== 演示模式 =====
    print("=" * 60)
    print("  简易数据库（基于文件）Demo")
    print("=" * 60)

    demo_dir = os.path.dirname(__file__)
    db = SimpleDB("demo_db", os.path.join(demo_dir, ".db_demo"))

    # 1. 建表
    print("\n--- 1. 建表 ---")
    db.create_table(
        "users",
        {
            "name": "str",
            "age": "int",
            "city": "str",
            "salary": "float",
        },
        primary_key="name",
    )

    db.create_table(
        "orders",
        {
            "user_name": "str",
            "product": "str",
            "amount": "float",
        },
    )

    # 2. 显示表
    print("\n--- 2. 显示所有表 ---")
    db.show_tables()

    # 3. 插入数据
    print("\n--- 3. 插入数据 ---")
    users = db.table("users")
    users.insert({"name": "张三", "age": 25, "city": "北京", "salary": 15000.0})
    users.insert({"name": "李四", "age": 30, "city": "上海", "salary": 20000.0})
    users.insert({"name": "王五", "age": 28, "city": "北京", "salary": 18000.0})
    users.insert({"name": "赵六", "age": 35, "city": "广州", "salary": 25000.0})
    users.insert({"name": "钱七", "age": 22, "city": "上海", "salary": 12000.0})

    orders = db.table("orders")
    orders.insert({"user_name": "张三", "product": "笔记本电脑", "amount": 6999.0})
    orders.insert({"user_name": "张三", "product": "鼠标", "amount": 99.0})
    orders.insert({"user_name": "李四", "product": "键盘", "amount": 399.0})
    orders.insert({"user_name": "王五", "product": "显示器", "amount": 2999.0})
    orders.insert({"user_name": "赵六", "product": "耳机", "amount": 899.0})

    # 4. 显示数据
    print("\n--- 4. 用户表 ---")
    users.display()
    print("\n--- 订单表 ---")
    orders.display()

    # 5. 查询
    print("\n--- 5. 查询：城市=北京 ---")
    results = users.select(where=lambda r: r["city"] == "北京")
    users.display(results)

    print("\n--- 6. 查询：年龄 > 25，按薪资降序 ---")
    results = users.select(where=lambda r: r["age"] > 25, order_by="-salary")
    users.display(results)

    print("\n--- 7. 查询：前 3 条 ---")
    results = users.select(limit=3)
    users.display(results)

    # 8. 更新
    print("\n--- 8. 更新：张三的薪资 ---")
    count = users.update(
        where=lambda r: r["name"] == "张三", updates={"salary": 16000.0}
    )
    print(f"更新了 {count} 条记录")
    users.display(users.select(where=lambda r: r["name"] == "张三"))

    # 9. 统计
    print("\n--- 9. 统计 ---")
    print(f"用户总数: {users.count()}")
    print(f"薪资总和: {users.aggregate('salary', 'sum')}")
    print(f"平均薪资: {users.aggregate('salary', 'avg')}")
    print(f"最高薪资: {users.aggregate('salary', 'max')}")

    # 10. 索引
    print("\n--- 10. 索引 ---")
    users.create_index("city")
    results = users.find_by_index("city", "上海")
    print("通过索引查找 city='上海':")
    users.display(results)

    # 11. 事务
    print("\n--- 11. 事务演示 ---")
    db.begin()
    users.insert({"name": "孙八", "age": 27, "city": "深圳", "salary": 17000.0})
    print(f"插入后用户数: {users.count()}")
    db.rollback()
    # 回滚后需要重新获取表引用（旧对象已失效）
    users = db.table("users")
    print(f"回滚后用户数: {users.count()}")

    db.begin()
    users.insert({"name": "孙八", "age": 27, "city": "深圳", "salary": 17000.0})
    db.commit()
    print(f"提交后用户数: {users.count()}")

    # 12. 表连接
    print("\n--- 12. 表连接 ---")
    joined = db.join("users", "orders", on=("name", "user_name"))
    print("用户 + 订单 连接结果:")
    for row in joined:
        print(f"  {row}")

    # 13. 删除
    print("\n--- 13. 删除：孙八 ---")
    count = users.delete(where=lambda r: r["name"] == "孙八")
    print(f"删除了 {count} 条记录")

    # 14. 最终数据
    print("\n--- 14. 最终用户表 ---")
    users.display()

    # 清理
    db.close()
    shutil.rmtree(os.path.join(demo_dir, ".db_demo"))

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
