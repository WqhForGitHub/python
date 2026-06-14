"""
命令行记账系统
功能：
    - 收入 / 支出记录的增删改查
    - 分类管理（餐饮、交通、购物、工资 ...）
    - 按日期/分类/类型筛选
    - 月度统计、分类统计、收支结余
    - JSON 持久化
    - 简单的 CLI 演示
"""

import os
import json
import uuid
from datetime import datetime, date
from collections import defaultdict


DEFAULT_CATEGORIES = {
    "expense": ["餐饮", "交通", "购物", "娱乐", "居住", "医疗", "教育", "其他"],
    "income": ["工资", "奖金", "兼职", "理财", "其他"],
}


class AccountBook:
    """记账本"""

    def __init__(self, filepath: str = "ledger.json"):
        self.filepath = filepath
        self.records = []
        self.categories = {k: list(v) for k, v in DEFAULT_CATEGORIES.items()}
        self._load()

    # -------- 持久化 --------
    def _load(self):
        if os.path.isfile(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.records = data.get("records", [])
                self.categories = data.get("categories", self.categories)
            except (json.JSONDecodeError, OSError):
                self.records = []

    def save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(
                {"records": self.records, "categories": self.categories},
                f, ensure_ascii=False, indent=2,
            )

    # -------- 增删改 --------
    def add(self, kind: str, amount: float, category: str,
            note: str = "", date_str: str = None) -> dict:
        if kind not in ("income", "expense"):
            raise ValueError("kind 必须是 income/expense")
        if amount <= 0:
            raise ValueError("金额必须 > 0")
        if category not in self.categories[kind]:
            self.categories[kind].append(category)

        rec = {
            "id": uuid.uuid4().hex[:8],
            "kind": kind,
            "amount": round(float(amount), 2),
            "category": category,
            "note": note,
            "date": date_str or date.today().isoformat(),
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        self.records.append(rec)
        self.save()
        return rec

    def delete(self, rec_id: str) -> bool:
        n = len(self.records)
        self.records = [r for r in self.records if r["id"] != rec_id]
        if len(self.records) < n:
            self.save()
            return True
        return False

    def update(self, rec_id: str, **fields) -> bool:
        for r in self.records:
            if r["id"] == rec_id:
                for k, v in fields.items():
                    if k in r and v is not None:
                        r[k] = v
                self.save()
                return True
        return False

    # -------- 查询 --------
    def query(self, kind: str = None, category: str = None,
              start: str = None, end: str = None) -> list:
        out = []
        for r in self.records:
            if kind and r["kind"] != kind:
                continue
            if category and r["category"] != category:
                continue
            if start and r["date"] < start:
                continue
            if end and r["date"] > end:
                continue
            out.append(r)
        return sorted(out, key=lambda x: x["date"])

    # -------- 统计 --------
    def summary(self, start: str = None, end: str = None) -> dict:
        records = self.query(start=start, end=end)
        income = sum(r["amount"] for r in records if r["kind"] == "income")
        expense = sum(r["amount"] for r in records if r["kind"] == "expense")
        return {
            "income": round(income, 2),
            "expense": round(expense, 2),
            "balance": round(income - expense, 2),
            "count": len(records),
        }

    def by_category(self, kind: str = "expense",
                    start: str = None, end: str = None) -> dict:
        records = self.query(kind=kind, start=start, end=end)
        agg = defaultdict(float)
        for r in records:
            agg[r["category"]] += r["amount"]
        return {k: round(v, 2) for k, v in
                sorted(agg.items(), key=lambda x: -x[1])}

    def by_month(self) -> dict:
        agg = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
        for r in self.records:
            ym = r["date"][:7]
            agg[ym][r["kind"]] += r["amount"]
        return {k: {"income": round(v["income"], 2),
                    "expense": round(v["expense"], 2),
                    "balance": round(v["income"] - v["expense"], 2)}
                for k, v in sorted(agg.items())}


# ==================== Demo ====================

def print_table(records: list):
    if not records:
        print("    (无记录)")
        return
    print(f"    {'日期':<12}{'类型':<6}{'分类':<8}{'金额':>10}  {'备注'}")
    print("    " + "-" * 50)
    for r in records:
        kind = "支出" if r["kind"] == "expense" else "收入"
        sign = "-" if r["kind"] == "expense" else "+"
        print(f"    {r['date']:<12}{kind:<6}{r['category']:<8}"
              f"{sign}{r['amount']:>8.2f}  {r['note']}")


if __name__ == "__main__":
    print("=" * 60)
    print("  命令行记账系统 Demo")
    print("=" * 60)

    base = os.path.dirname(os.path.abspath(__file__))
    db_file = os.path.join(base, "demo_ledger.json")
    if os.path.exists(db_file):
        os.remove(db_file)

    book = AccountBook(db_file)

    # 1. 添加记录
    print("\n--- 1. 添加记录 ---")
    book.add("income",  10000, "工资", "10月份工资", "2025-10-05")
    book.add("expense",  35.5, "餐饮", "早餐午餐",  "2025-10-06")
    book.add("expense",  120,  "餐饮", "聚餐",      "2025-10-07")
    book.add("expense",  15,   "交通", "地铁",      "2025-10-07")
    book.add("expense",  299,  "购物", "买衣服",    "2025-10-08")
    book.add("expense",  68,   "娱乐", "电影票",    "2025-10-09")
    book.add("income",   500,  "兼职", "周末兼职",  "2025-10-12")
    book.add("expense",  1500, "居住", "水电房租",  "2025-10-15")
    book.add("expense",  88,   "餐饮", "外卖",      "2025-11-02")
    book.add("income",   10000,"工资", "11月份工资","2025-11-05")
    print(f"  共添加 {len(book.records)} 条记录")

    # 2. 查询
    print("\n--- 2. 查询 10 月所有支出 ---")
    rs = book.query(kind="expense", start="2025-10-01", end="2025-10-31")
    print_table(rs)

    # 3. 总览
    print("\n--- 3. 全部账目总览 ---")
    s = book.summary()
    print(f"  总收入: {s['income']:>10.2f}")
    print(f"  总支出: {s['expense']:>10.2f}")
    print(f"  结余:   {s['balance']:>10.2f}")
    print(f"  记录数: {s['count']}")

    # 4. 分类统计
    print("\n--- 4. 支出分类统计 ---")
    for cat, amt in book.by_category("expense").items():
        bar = "█" * int(amt / 50)
        print(f"  {cat:<6} {amt:>8.2f}  {bar}")

    # 5. 月度统计
    print("\n--- 5. 月度统计 ---")
    print(f"  {'月份':<10}{'收入':>10}{'支出':>10}{'结余':>10}")
    for ym, v in book.by_month().items():
        print(f"  {ym:<10}{v['income']:>10.2f}{v['expense']:>10.2f}{v['balance']:>10.2f}")

    # 6. 修改 / 删除
    print("\n--- 6. 修改与删除 ---")
    target = book.records[0]["id"]
    book.update(target, note="10月份工资(已修改)")
    print(f"  修改记录 {target}")
    book.delete(book.records[-1]["id"])
    print(f"  删除最后一条，当前剩 {len(book.records)} 条")

    # 清理
    if os.path.exists(db_file):
        os.remove(db_file)

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
