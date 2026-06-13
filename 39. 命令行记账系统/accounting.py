"""
命令行记账系统
功能：命令行收支记账系统，支持记录收入/支出、分类、查询、月报、
      预算管理、CSV 导入/导出、JSON 持久化、统计分析等
"""

import os
import json
import csv
import uuid
from datetime import datetime, timedelta
from collections import defaultdict


class Transaction:
    """单笔交易"""

    INCOME = "income"
    EXPENSE = "expense"

    def __init__(self, amount: float, category: str, txn_type: str,
                 note: str = "", date: str = None, txn_id: str = None):
        self.id = txn_id or uuid.uuid4().hex[:8]
        self.amount = float(amount)
        self.category = category
        self.type = txn_type
        self.note = note
        self.date = date or datetime.now().strftime("%Y-%m-%d")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "amount": self.amount,
            "category": self.category,
            "type": self.type,
            "note": self.note,
            "date": self.date,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Transaction":
        return cls(
            amount=d["amount"],
            category=d["category"],
            txn_type=d["type"],
            note=d.get("note", ""),
            date=d.get("date"),
            txn_id=d.get("id"),
        )

    @property
    def signed_amount(self) -> float:
        return self.amount if self.type == self.INCOME else -self.amount

    def __str__(self):
        sign = "+" if self.type == self.INCOME else "-"
        return (f"[{self.id}] {self.date}  {sign}{self.amount:>8.2f}  "
                f"{self.category:<8} {self.note}")


class Ledger:
    """账本"""

    DEFAULT_INCOME_CATEGORIES = ["工资", "奖金", "投资", "兼职", "其他收入"]
    DEFAULT_EXPENSE_CATEGORIES = ["餐饮", "交通", "购物", "娱乐", "住房",
                                  "医疗", "教育", "通讯", "其他支出"]

    def __init__(self, data_file: str = "ledger.json"):
        self.data_file = data_file
        self.transactions = []
        # 月度预算 {"2024-01": {"餐饮": 1000, ...}}
        self.budgets = {}
        self.load()

    # ==================== 持久化 ====================

    def load(self):
        if not os.path.exists(self.data_file):
            return
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.transactions = [Transaction.from_dict(t)
                                for t in data.get("transactions", [])]
            self.budgets = data.get("budgets", {})
        except (json.JSONDecodeError, KeyError) as e:
            print(f"[警告] 加载账本失败: {e}")

    def save(self):
        data = {
            "transactions": [t.to_dict() for t in self.transactions],
            "budgets": self.budgets,
            "saved_at": datetime.now().isoformat(),
        }
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ==================== 交易管理 ====================

    def add(self, amount: float, category: str, txn_type: str,
            note: str = "", date: str = None) -> Transaction:
        """添加交易"""
        if amount <= 0:
            raise ValueError("金额必须大于 0")
        if txn_type not in (Transaction.INCOME, Transaction.EXPENSE):
            raise ValueError(f"无效类型: {txn_type}")
        if date:
            datetime.strptime(date, "%Y-%m-%d")  # 验证格式

        txn = Transaction(amount, category, txn_type, note, date)
        self.transactions.append(txn)
        self.save()
        return txn

    def add_income(self, amount: float, category: str = "其他收入",
                   note: str = "", date: str = None) -> Transaction:
        return self.add(amount, category, Transaction.INCOME, note, date)

    def add_expense(self, amount: float, category: str = "其他支出",
                    note: str = "", date: str = None) -> Transaction:
        return self.add(amount, category, Transaction.EXPENSE, note, date)

    def remove(self, txn_id: str) -> bool:
        """删除交易"""
        for i, t in enumerate(self.transactions):
            if t.id == txn_id:
                del self.transactions[i]
                self.save()
                return True
        return False

    def update(self, txn_id: str, **kwargs) -> bool:
        """修改交易"""
        for t in self.transactions:
            if t.id == txn_id:
                for k, v in kwargs.items():
                    if hasattr(t, k) and v is not None:
                        setattr(t, k, v)
                self.save()
                return True
        return False

    # ==================== 查询 ====================

    def query(self, start_date: str = None, end_date: str = None,
              category: str = None, txn_type: str = None,
              keyword: str = None) -> list:
        """多条件查询"""
        results = self.transactions

        if start_date:
            results = [t for t in results if t.date >= start_date]
        if end_date:
            results = [t for t in results if t.date <= end_date]
        if category:
            results = [t for t in results if t.category == category]
        if txn_type:
            results = [t for t in results if t.type == txn_type]
        if keyword:
            kw = keyword.lower()
            results = [t for t in results
                      if kw in t.note.lower() or kw in t.category.lower()]

        return sorted(results, key=lambda t: t.date)

    def get_by_month(self, year_month: str) -> list:
        """按月份获取交易，year_month 如 '2024-01'"""
        return [t for t in self.transactions if t.date.startswith(year_month)]

    # ==================== 统计 ====================

    def total_income(self, transactions: list = None) -> float:
        txns = transactions if transactions is not None else self.transactions
        return sum(t.amount for t in txns if t.type == Transaction.INCOME)

    def total_expense(self, transactions: list = None) -> float:
        txns = transactions if transactions is not None else self.transactions
        return sum(t.amount for t in txns if t.type == Transaction.EXPENSE)

    def balance(self, transactions: list = None) -> float:
        txns = transactions if transactions is not None else self.transactions
        return sum(t.signed_amount for t in txns)

    def category_summary(self, transactions: list = None,
                         txn_type: str = None) -> dict:
        """分类汇总"""
        txns = transactions if transactions is not None else self.transactions
        if txn_type:
            txns = [t for t in txns if t.type == txn_type]
        result = defaultdict(float)
        for t in txns:
            result[t.category] += t.amount
        return dict(result)

    def monthly_report(self, year_month: str) -> dict:
        """月度报表"""
        txns = self.get_by_month(year_month)
        return {
            "month": year_month,
            "transaction_count": len(txns),
            "total_income": self.total_income(txns),
            "total_expense": self.total_expense(txns),
            "balance": self.balance(txns),
            "income_by_category": self.category_summary(txns, Transaction.INCOME),
            "expense_by_category": self.category_summary(txns, Transaction.EXPENSE),
        }

    def daily_average(self, year_month: str) -> dict:
        """日均收支"""
        txns = self.get_by_month(year_month)
        if not txns:
            return {"days": 0, "avg_income": 0, "avg_expense": 0}
        days = len({t.date for t in txns})
        return {
            "days": days,
            "avg_income": self.total_income(txns) / days,
            "avg_expense": self.total_expense(txns) / days,
        }

    # ==================== 预算 ====================

    def set_budget(self, year_month: str, category: str, amount: float):
        if year_month not in self.budgets:
            self.budgets[year_month] = {}
        self.budgets[year_month][category] = amount
        self.save()

    def check_budget(self, year_month: str) -> dict:
        """检查预算执行情况"""
        if year_month not in self.budgets:
            return {}
        spent = self.category_summary(self.get_by_month(year_month),
                                      Transaction.EXPENSE)
        result = {}
        for cat, budget in self.budgets[year_month].items():
            used = spent.get(cat, 0)
            result[cat] = {
                "budget": budget,
                "spent": used,
                "remaining": budget - used,
                "percent": (used / budget * 100) if budget > 0 else 0,
                "over": used > budget,
            }
        return result

    # ==================== 导入导出 ====================

    def export_csv(self, filepath: str):
        with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "date", "type", "category", "amount", "note"])
            for t in sorted(self.transactions, key=lambda x: x.date):
                writer.writerow([t.id, t.date, t.type, t.category,
                                t.amount, t.note])

    def import_csv(self, filepath: str) -> int:
        count = 0
        with open(filepath, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    self.add(
                        amount=float(row["amount"]),
                        category=row["category"],
                        txn_type=row["type"],
                        note=row.get("note", ""),
                        date=row.get("date"),
                    )
                    count += 1
                except (ValueError, KeyError) as e:
                    print(f"[跳过] 行: {row} - {e}")
        return count

    # ==================== 显示 ====================

    @staticmethod
    def print_table(transactions: list, title: str = "交易列表"):
        print(f"\n--- {title} ({len(transactions)} 条) ---")
        if not transactions:
            print("  (无)")
            return
        print(f"  {'ID':<10}{'日期':<12}{'金额':>10}  {'类别':<10}备注")
        print(f"  {'-' * 60}")
        for t in transactions:
            sign = "+" if t.type == Transaction.INCOME else "-"
            print(f"  {t.id:<10}{t.date:<12}{sign}{t.amount:>9.2f}  "
                  f"{t.category:<10}{t.note}")

    def print_summary(self, transactions: list = None,
                      title: str = "总体汇总"):
        txns = transactions if transactions is not None else self.transactions
        income = self.total_income(txns)
        expense = self.total_expense(txns)
        bal = income - expense
        print(f"\n--- {title} ---")
        print(f"  交易笔数: {len(txns)}")
        print(f"  总收入:   {income:>10.2f}")
        print(f"  总支出:   {expense:>10.2f}")
        print(f"  结余:     {bal:>10.2f}")

    @staticmethod
    def print_monthly_report(report: dict):
        print(f"\n=== {report['month']} 月度报表 ===")
        print(f"  交易笔数: {report['transaction_count']}")
        print(f"  总收入:   {report['total_income']:.2f}")
        print(f"  总支出:   {report['total_expense']:.2f}")
        print(f"  结余:     {report['balance']:.2f}")

        if report["income_by_category"]:
            print("  收入构成:")
            for cat, amt in sorted(report["income_by_category"].items(),
                                   key=lambda x: -x[1]):
                print(f"    {cat:<10}{amt:>10.2f}")

        if report["expense_by_category"]:
            print("  支出构成:")
            total = report["total_expense"] or 1
            for cat, amt in sorted(report["expense_by_category"].items(),
                                   key=lambda x: -x[1]):
                pct = amt / total * 100
                bar = "#" * int(pct / 2.5)
                print(f"    {cat:<10}{amt:>10.2f}  {pct:>5.1f}%  {bar}")

    @staticmethod
    def print_budget_check(check: dict, year_month: str):
        print(f"\n=== {year_month} 预算执行 ===")
        if not check:
            print("  (未设置预算)")
            return
        for cat, info in check.items():
            status = "[超支!]" if info["over"] else "[正常]"
            print(f"  {cat:<10}预算 {info['budget']:>8.2f}  "
                  f"已用 {info['spent']:>8.2f}  "
                  f"({info['percent']:>5.1f}%)  {status}")


# ==================== CLI 交互 ====================

def interactive_cli(ledger: Ledger):
    """交互式命令行"""
    print("\n命令: add(添加) list(列出) report(月报) budget(预算) "
          "del(删除) export(导出) quit(退出)")
    while True:
        try:
            cmd = input("\n> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break
        if cmd in ("quit", "q", "exit"):
            break
        elif cmd == "list":
            Ledger.print_table(ledger.transactions, "全部交易")
            ledger.print_summary()
        elif cmd.startswith("add"):
            try:
                t = input("类型 (income/expense): ").strip()
                amt = float(input("金额: ").strip())
                cat = input("类别: ").strip()
                note = input("备注: ").strip()
                ledger.add(amt, cat, t, note)
                print("已添加。")
            except ValueError as e:
                print(f"输入有误: {e}")
        elif cmd == "report":
            ym = input("年-月 (如 2024-01): ").strip()
            Ledger.print_monthly_report(ledger.monthly_report(ym))
        elif cmd == "budget":
            ym = input("年-月: ").strip()
            Ledger.print_budget_check(ledger.check_budget(ym), ym)
        elif cmd.startswith("del"):
            tid = input("交易ID: ").strip()
            print("删除成功" if ledger.remove(tid) else "未找到")
        elif cmd == "export":
            fp = input("导出路径: ").strip()
            ledger.export_csv(fp)
            print(f"已导出至 {fp}")
        else:
            print("未知命令")


# ==================== 演示 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("  命令行记账系统 Demo")
    print("=" * 60)

    base_dir = os.path.dirname(__file__)
    data_file = os.path.join(base_dir, "demo_ledger.json")

    # 清理旧数据
    if os.path.exists(data_file):
        os.remove(data_file)

    ledger = Ledger(data_file)

    # 1. 添加交易
    print("\n--- 1. 添加交易 ---")
    ledger.add_income(8000, "工资", "1月工资", date="2024-01-05")
    ledger.add_income(500, "奖金", "项目奖金", date="2024-01-10")
    ledger.add_expense(1500, "住房", "1月房租", date="2024-01-01")
    ledger.add_expense(300, "餐饮", "外卖", date="2024-01-02")
    ledger.add_expense(50, "交通", "地铁", date="2024-01-03")
    ledger.add_expense(800, "购物", "买衣服", date="2024-01-15")
    ledger.add_expense(120, "餐饮", "火锅聚餐", date="2024-01-20")
    ledger.add_expense(80, "娱乐", "电影票", date="2024-01-22")

    ledger.add_income(9000, "工资", "2月工资", date="2024-02-05")
    ledger.add_expense(1500, "住房", "2月房租", date="2024-02-01")
    ledger.add_expense(400, "餐饮", "日常吃饭", date="2024-02-10")
    ledger.add_expense(200, "交通", "打车", date="2024-02-12")
    ledger.add_expense(2000, "购物", "电子产品", date="2024-02-15")

    print(f"已添加 {len(ledger.transactions)} 条交易记录")

    # 2. 列出全部 + 总览
    Ledger.print_table(ledger.transactions, "全部交易")
    ledger.print_summary()

    # 3. 多条件查询
    print("\n--- 3. 查询 1 月支出 ---")
    results = ledger.query(start_date="2024-01-01", end_date="2024-01-31",
                           txn_type=Transaction.EXPENSE)
    Ledger.print_table(results, "1月支出")

    # 4. 关键词查询
    print("\n--- 4. 关键词查询: '餐' ---")
    results = ledger.query(keyword="餐")
    Ledger.print_table(results, "餐相关")

    # 5. 月度报表
    Ledger.print_monthly_report(ledger.monthly_report("2024-01"))
    Ledger.print_monthly_report(ledger.monthly_report("2024-02"))

    # 6. 日均收支
    print("\n--- 6. 1月日均收支 ---")
    avg = ledger.daily_average("2024-01")
    print(f"  涉及天数: {avg['days']}")
    print(f"  日均收入: {avg['avg_income']:.2f}")
    print(f"  日均支出: {avg['avg_expense']:.2f}")

    # 7. 预算
    print("\n--- 7. 设置 1 月预算 ---")
    ledger.set_budget("2024-01", "餐饮", 500)
    ledger.set_budget("2024-01", "购物", 1000)
    ledger.set_budget("2024-01", "娱乐", 200)
    ledger.set_budget("2024-01", "交通", 300)
    Ledger.print_budget_check(ledger.check_budget("2024-01"), "2024-01")

    # 8. 修改和删除
    print("\n--- 8. 修改和删除 ---")
    first_id = ledger.transactions[0].id
    print(f"修改 {first_id} 的备注...")
    ledger.update(first_id, note="1月工资（已到账）")
    print(f"删除 {ledger.transactions[-1].id}...")
    ledger.remove(ledger.transactions[-1].id)
    print(f"剩余交易数: {len(ledger.transactions)}")

    # 9. 导出 CSV
    print("\n--- 9. 导出 CSV ---")
    csv_file = os.path.join(base_dir, "demo_ledger.csv")
    ledger.export_csv(csv_file)
    print(f"已导出: {csv_file}")
    with open(csv_file, "r", encoding="utf-8-sig") as f:
        print("CSV 前 5 行:")
        for i, line in enumerate(f):
            if i >= 5:
                break
            print(f"  {line.rstrip()}")

    # 10. 重新加载（持久化验证）
    print("\n--- 10. 重新加载持久化数据 ---")
    ledger2 = Ledger(data_file)
    print(f"重新加载后交易数: {len(ledger2.transactions)}")
    ledger2.print_summary(title="重载后汇总")

    # 清理
    for fp in [data_file, csv_file]:
        if os.path.exists(fp):
            os.remove(fp)

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
    print("\n要进入交互模式：")
    print("  ledger = Ledger('my_ledger.json'); interactive_cli(ledger)")
