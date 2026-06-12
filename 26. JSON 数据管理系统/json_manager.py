"""
JSON 数据管理系统
功能：对 JSON 数据进行增删改查、搜索、排序、筛选、导入导出等操作
"""

import json
import os
from datetime import datetime


class JsonDataManager:
    """JSON 数据管理器"""

    def __init__(self, filepath="data.json"):
        self.filepath = filepath
        self.data = []
        self._load()

    # ==================== 基础 IO ====================

    def _load(self):
        """从文件加载数据"""
        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as f:
                try:
                    self.data = json.load(f)
                    if not isinstance(self.data, list):
                        self.data = [self.data]
                except json.JSONDecodeError:
                    self.data = []
        else:
            self.data = []

    def _save(self):
        """保存数据到文件"""
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    # ==================== CRUD 操作 ====================

    def add(self, record: dict) -> int:
        """添加一条记录，自动生成 id 和时间戳"""
        if not isinstance(record, dict):
            raise ValueError("记录必须是字典类型")
        record["_id"] = max((r.get("_id", 0) for r in self.data), default=0) + 1
        record["_created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record["_updated_at"] = record["_created_at"]
        self.data.append(record)
        self._save()
        return record["_id"]

    def add_batch(self, records: list) -> list:
        """批量添加记录"""
        ids = []
        for record in records:
            ids.append(self.add(record))
        return ids

    def get_by_id(self, record_id: int) -> dict | None:
        """根据 ID 获取记录"""
        for record in self.data:
            if record.get("_id") == record_id:
                return record
        return None

    def update(self, record_id: int, updates: dict) -> bool:
        """更新指定 ID 的记录"""
        for record in self.data:
            if record.get("_id") == record_id:
                record.update(updates)
                record["_updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self._save()
                return True
        return False

    def delete(self, record_id: int) -> bool:
        """删除指定 ID 的记录"""
        for i, record in enumerate(self.data):
            if record.get("_id") == record_id:
                self.data.pop(i)
                self._save()
                return True
        return False

    def delete_all(self):
        """清空所有数据"""
        self.data = []
        self._save()

    # ==================== 查询操作 ====================

    def find(self, **conditions) -> list:
        """按条件查询（支持精确匹配和函数匹配）
        示例: find(name="张三")  find(age=lambda x: x > 20)
        """
        results = []
        for record in self.data:
            match = True
            for key, expected in conditions.items():
                if key not in record:
                    match = False
                    break
                if callable(expected):
                    if not expected(record[key]):
                        match = False
                        break
                elif record[key] != expected:
                    match = False
                    break
            if match:
                results.append(record)
        return results

    def find_one(self, **conditions) -> dict | None:
        """查询第一条匹配记录"""
        results = self.find(**conditions)
        return results[0] if results else None

    def search(self, keyword: str, fields: list = None) -> list:
        """关键字搜索（模糊匹配）"""
        results = []
        keyword_lower = keyword.lower()
        for record in self.data:
            for key, value in record.items():
                if fields and key not in fields:
                    continue
                if keyword_lower in str(value).lower():
                    results.append(record)
                    break
        return results

    def sort(self, key: str, reverse: bool = False) -> list:
        """按指定字段排序"""
        return sorted(self.data, key=lambda r: r.get(key, ""), reverse=reverse)

    def count(self, **conditions) -> int:
        """统计符合条件的记录数"""
        if not conditions:
            return len(self.data)
        return len(self.find(**conditions))

    # ==================== 聚合操作 ====================

    def distinct(self, field: str) -> list:
        """获取指定字段的所有不重复值"""
        values = set()
        for record in self.data:
            if field in record:
                values.add(record[field])
        return list(values)

    def group_count(self, field: str) -> dict:
        """按字段分组统计数量"""
        groups = {}
        for record in self.data:
            value = record.get(field, "未分类")
            groups[value] = groups.get(value, 0) + 1
        return groups

    def aggregate(self, field: str, func: str) -> float | None:
        """聚合计算: sum, avg, min, max"""
        values = [
            r[field]
            for r in self.data
            if field in r and isinstance(r[field], (int, float))
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
        else:
            raise ValueError(f"不支持的聚合函数: {func}，可选: sum, avg, min, max")

    # ==================== 导入导出 ====================

    def export_to(self, filepath: str):
        """导出数据到指定文件"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def import_from(self, filepath: str) -> int:
        """从文件导入数据，返回导入数量"""
        with open(filepath, "r", encoding="utf-8") as f:
            imported = json.load(f)
        if isinstance(imported, dict):
            imported = [imported]
        count = 0
        for record in imported:
            if isinstance(record, dict):
                self.add(record)
                count += 1
        return count

    # ==================== 输出 ====================

    def display(self, records: list = None, fields: list = None):
        """格式化显示记录"""
        data = records if records is not None else self.data
        if not data:
            print("  (无数据)")
            return

        display_data = []
        for record in data:
            if fields:
                display_data.append(
                    {k: record.get(k, "") for k in fields if k in record}
                )
            else:
                display_data.append(record)

        print(json.dumps(display_data, ensure_ascii=False, indent=2))


def interactive_menu():
    """交互式菜单"""
    db = JsonDataManager()

    while True:
        print("\n" + "=" * 50)
        print("       JSON 数据管理系统")
        print("=" * 50)
        print("  1. 添加记录")
        print("  2. 批量添加记录")
        print("  3. 查看/搜索记录")
        print("  4. 更新记录")
        print("  5. 删除记录")
        print("  6. 排序")
        print("  7. 统计与聚合")
        print("  8. 导入/导出")
        print("  9. 显示所有记录")
        print("  0. 退出")
        print("=" * 50)

        choice = input("请选择操作: ").strip()

        if choice == "1":
            print('输入 JSON 格式记录，例如: {"name": "张三", "age": 25}')
            try:
                record = json.loads(input("记录: ").strip())
                rid = db.add(record)
                print(f"添加成功，ID: {rid}")
            except (json.JSONDecodeError, ValueError) as e:
                print(f"输入错误: {e}")

        elif choice == "2":
            print('输入 JSON 数组，例如: [{"name": "A"}, {"name": "B"}]')
            try:
                records = json.loads(input("记录: ").strip())
                ids = db.add_batch(records)
                print(f"批量添加成功，共 {len(ids)} 条，IDs: {ids}")
            except (json.JSONDecodeError, ValueError) as e:
                print(f"输入错误: {e}")

        elif choice == "3":
            print("  a. 按 ID 查询")
            print("  b. 按条件查询")
            print("  c. 关键字搜索")
            sub = input("选择: ").strip().lower()
            if sub == "a":
                rid = int(input("ID: ").strip())
                record = db.get_by_id(rid)
                db.display([record] if record else [])
            elif sub == "b":
                print(
                    '输入查询条件 JSON，例如: {"age": 25} 或 {"age": "lambda x: x>20"}'
                )
                try:
                    cond = json.loads(input("条件: ").strip())
                    for k, v in cond.items():
                        if isinstance(v, str) and v.startswith("lambda"):
                            cond[k] = eval(v)
                    results = db.find(**cond)
                    db.display(results)
                except Exception as e:
                    print(f"查询错误: {e}")
            elif sub == "c":
                keyword = input("关键字: ").strip()
                results = db.search(keyword)
                db.display(results)

        elif choice == "4":
            rid = int(input("要更新的记录 ID: ").strip())
            print('输入更新内容 JSON，例如: {"age": 26}')
            try:
                updates = json.loads(input("更新: ").strip())
                if db.update(rid, updates):
                    print("更新成功")
                else:
                    print("未找到该记录")
            except json.JSONDecodeError as e:
                print(f"输入错误: {e}")

        elif choice == "5":
            rid = int(input("要删除的记录 ID: ").strip())
            if db.delete(rid):
                print("删除成功")
            else:
                print("未找到该记录")

        elif choice == "6":
            field = input("排序字段: ").strip()
            order = input("升序(a)/降序(d): ").strip().lower()
            results = db.sort(field, reverse=(order == "d"))
            db.display(results)

        elif choice == "7":
            print("  a. 记录总数")
            print("  b. 分组统计")
            print("  c. 聚合计算")
            sub = input("选择: ").strip().lower()
            if sub == "a":
                print(f"总记录数: {db.count()}")
            elif sub == "b":
                field = input("分组字段: ").strip()
                result = db.group_count(field)
                for k, v in result.items():
                    print(f"  {k}: {v}")
            elif sub == "c":
                field = input("聚合字段: ").strip()
                func = input("函数(sum/avg/min/max): ").strip()
                result = db.aggregate(field, func)
                print(f"{func}({field}) = {result}")

        elif choice == "8":
            print("  a. 导出")
            print("  b. 导入")
            sub = input("选择: ").strip().lower()
            if sub == "a":
                path = input("导出路径: ").strip()
                db.export_to(path)
                print(f"已导出到 {path}")
            elif sub == "b":
                path = input("导入路径: ").strip()
                count = db.import_from(path)
                print(f"已导入 {count} 条记录")

        elif choice == "9":
            db.display()

        elif choice == "0":
            print("再见！")
            break


if __name__ == "__main__":
    # ===== 演示模式 =====
    print("=" * 60)
    print("  JSON 数据管理系统 Demo")
    print("=" * 60)

    db = JsonDataManager("demo_data.json")

    # 1. 添加数据
    print("\n--- 添加数据 ---")
    id1 = db.add({"name": "张三", "age": 25, "city": "北京", "salary": 15000})
    id2 = db.add({"name": "李四", "age": 30, "city": "上海", "salary": 20000})
    id3 = db.add({"name": "王五", "age": 28, "city": "北京", "salary": 18000})
    id4 = db.add({"name": "赵六", "age": 35, "city": "广州", "salary": 25000})
    id5 = db.add({"name": "钱七", "age": 22, "city": "上海", "salary": 12000})
    print(f"已添加 5 条记录，IDs: {[id1, id2, id3, id4, id5]}")

    # 2. 查看所有数据
    print("\n--- 所有数据 ---")
    db.display()

    # 3. 按 ID 查询
    print(f"\n--- 查询 ID={id2} 的记录 ---")
    record = db.get_by_id(id2)
    db.display([record])

    # 4. 条件查询
    print("\n--- 查询 city='北京' 的记录 ---")
    results = db.find(city="北京")
    db.display(results)

    # 5. 函数条件查询
    print("\n--- 查询 age > 25 的记录 ---")
    results = db.find(age=lambda x: x > 25)
    db.display(results)

    # 6. 关键字搜索
    print("\n--- 搜索关键字 '上海' ---")
    results = db.search("上海")
    db.display(results)

    # 7. 排序
    print("\n--- 按 salary 降序 ---")
    results = db.sort("salary", reverse=True)
    db.display(results)

    # 8. 更新
    print(f"\n--- 更新 ID={id1} 的 salary 为 16000 ---")
    db.update(id1, {"salary": 16000})
    db.display([db.get_by_id(id1)])

    # 9. 统计与聚合
    print("\n--- 统计 ---")
    print(f"总记录数: {db.count()}")
    print(f"按城市分组: {db.group_count('city')}")
    print(f"薪资总和: {db.aggregate('salary', 'sum')}")
    print(f"平均薪资: {db.aggregate('salary', 'avg')}")
    print(f"最高薪资: {db.aggregate('salary', 'max')}")
    print(f"最低薪资: {db.aggregate('salary', 'min')}")
    print(f"不重复城市: {db.distinct('city')}")

    # 10. 删除
    print(f"\n--- 删除 ID={id3} ---")
    db.delete(id3)
    print(f"剩余记录数: {db.count()}")

    # 11. 导出
    print("\n--- 导出数据 ---")
    export_path = os.path.join(os.path.dirname(__file__), "export_demo.json")
    db.export_to(export_path)
    print(f"已导出到 {export_path}")

    # 12. 删除演示
    print(f"\n--- 删除 ID={id5} ---")
    db.delete(id5)

    # 最终数据
    print("\n--- 最终数据 ---")
    db.display()

    # 清理演示文件
    os.remove("demo_data.json")
    os.remove(export_path)

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！如需交互式操作，请取消注释 interactive_menu()")
    print("=" * 60)

    # 如需交互式操作，取消注释下面这行
    # interactive_menu()
