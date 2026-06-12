"""
CSV 数据分析工具
功能：读取 CSV 文件，进行筛选、排序、统计、聚合、去重、合并等分析操作
"""

import csv
import os
import math
from collections import Counter, defaultdict


class CsvAnalyzer:
    """CSV 数据分析器"""

    def __init__(self, filepath: str = None, encoding: str = "utf-8"):
        self.headers = []
        self.rows = []
        self.filepath = filepath
        self.encoding = encoding
        if filepath:
            self.load(filepath, encoding)

    # ==================== IO 操作 ====================

    def load(self, filepath: str, encoding: str = "utf-8"):
        """加载 CSV 文件"""
        self.filepath = filepath
        self.encoding = encoding
        with open(filepath, "r", encoding=encoding, newline="") as f:
            reader = csv.DictReader(f)
            self.headers = reader.fieldnames or []
            self.rows = [dict(row) for row in reader]
        print(f"已加载 {filepath}，共 {len(self.rows)} 行，{len(self.headers)} 列")
        print(f"列名: {list(self.headers)}")

    def save(self, filepath: str, encoding: str = "utf-8"):
        """保存为 CSV 文件"""
        with open(filepath, "w", encoding=encoding, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.headers)
            writer.writeheader()
            writer.writerows(self.rows)
        print(f"已保存到 {filepath}，共 {len(self.rows)} 行")

    @classmethod
    def from_data(cls, headers: list, rows: list) -> "CsvAnalyzer":
        """从内存数据创建"""
        analyzer = cls()
        analyzer.headers = headers
        analyzer.rows = rows
        return analyzer

    # ==================== 数据预览 ====================

    def head(self, n: int = 5) -> list:
        """查看前 n 行"""
        return self.rows[:n]

    def tail(self, n: int = 5) -> list:
        """查看后 n 行"""
        return self.rows[-n:]

    def info(self):
        """数据概览"""
        print(f"行数: {len(self.rows)}")
        print(f"列数: {len(self.headers)}")
        print(f"列名: {list(self.headers)}")
        print("-" * 60)
        for col in self.headers:
            non_empty = sum(1 for r in self.rows if r.get(col, "").strip())
            values = [r[col] for r in self.rows if r.get(col, "").strip()]
            dtype = "数值" if self._is_numeric(col) else "文本"
            unique = len(set(values))
            print(f"  {col}: 类型={dtype}, 非空={non_empty}, 唯一值={unique}")

    def _is_numeric(self, col: str) -> bool:
        """判断某列是否为数值类型"""
        count = 0
        for r in self.rows:
            val = r.get(col, "").strip()
            if val:
                try:
                    float(val)
                    count += 1
                except ValueError:
                    return False
        return count > 0

    def _to_float(self, value) -> float | None:
        """安全转换为浮点数"""
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    # ==================== 筛选 ====================

    def filter(self, condition: callable) -> "CsvAnalyzer":
        """按条件筛选行，condition 是一个接收 dict 返回 bool 的函数"""
        filtered = [r for r in self.rows if condition(r)]
        return CsvAnalyzer.from_data(self.headers, filtered)

    def filter_eq(self, column: str, value) -> "CsvAnalyzer":
        """精确匹配筛选"""
        return self.filter(lambda r: r.get(column) == str(value))

    def filter_gt(self, column: str, value) -> "CsvAnalyzer":
        """大于筛选（数值列）"""
        return self.filter(
            lambda r: self._to_float(r.get(column)) is not None
            and self._to_float(r.get(column)) > float(value)
        )

    def filter_lt(self, column: str, value) -> "CsvAnalyzer":
        """小于筛选（数值列）"""
        return self.filter(
            lambda r: self._to_float(r.get(column)) is not None
            and self._to_float(r.get(column)) < float(value)
        )

    def filter_contains(self, column: str, keyword: str) -> "CsvAnalyzer":
        """包含关键字筛选"""
        return self.filter(lambda r: keyword.lower() in r.get(column, "").lower())

    def filter_between(self, column: str, low, high) -> "CsvAnalyzer":
        """区间筛选"""
        return self.filter(lambda r: low <= self._to_float(r.get(column)) <= high)

    # ==================== 排序 ====================

    def sort_by(self, column: str, reverse: bool = False) -> "CsvAnalyzer":
        """按列排序"""
        if self._is_numeric(column):
            sorted_rows = sorted(
                self.rows,
                key=lambda r: self._to_float(r.get(column, "")) or 0,
                reverse=reverse,
            )
        else:
            sorted_rows = sorted(
                self.rows, key=lambda r: r.get(column, ""), reverse=reverse
            )
        return CsvAnalyzer.from_data(self.headers, sorted_rows)

    # ==================== 统计分析 ====================

    def describe(self, column: str = None):
        """描述性统计"""
        if column:
            self._describe_column(column)
        else:
            for col in self.headers:
                if self._is_numeric(col):
                    self._describe_column(col)

    def _describe_column(self, col: str):
        """对单列进行描述性统计"""
        values = [
            self._to_float(r[col])
            for r in self.rows
            if self._to_float(r.get(col)) is not None
        ]
        if not values:
            print(f"{col}: 无数值数据")
            return

        n = len(values)
        mean = sum(values) / n
        sorted_vals = sorted(values)
        median = (
            sorted_vals[n // 2]
            if n % 2
            else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
        )
        variance = sum((x - mean) ** 2 for x in values) / n
        std_dev = math.sqrt(variance)

        print(f"\n--- {col} 统计 ---")
        print(f"  数量:   {n}")
        print(f"  总和:   {sum(values):.2f}")
        print(f"  均值:   {mean:.2f}")
        print(f"  中位数: {median:.2f}")
        print(f"  标准差: {std_dev:.2f}")
        print(f"  最小值: {min(values):.2f}")
        print(f"  最大值: {max(values):.2f}")
        q1 = sorted_vals[n // 4]
        q3 = sorted_vals[3 * n // 4]
        print(f"  Q1:     {q1:.2f}")
        print(f"  Q3:     {q3:.2f}")

    def value_counts(self, column: str, top_n: int = None) -> dict:
        """统计某列各值出现次数"""
        counter = Counter(r.get(column, "") for r in self.rows)
        result = dict(counter.most_common(top_n))
        for k, v in result.items():
            print(f"  {k}: {v} ({v / len(self.rows) * 100:.1f}%)")
        return result

    def group_aggregate(self, group_col: str, agg_col: str, func: str = "mean") -> dict:
        """分组聚合"""
        groups = defaultdict(list)
        for r in self.rows:
            key = r.get(group_col, "未分类")
            val = self._to_float(r.get(agg_col))
            if val is not None:
                groups[key].append(val)

        results = {}
        for key, values in groups.items():
            if func == "mean":
                results[key] = sum(values) / len(values)
            elif func == "sum":
                results[key] = sum(values)
            elif func == "count":
                results[key] = len(values)
            elif func == "min":
                results[key] = min(values)
            elif func == "max":
                results[key] = max(values)

        print(f"\n--- 按 {group_col} 分组，{func}({agg_col}) ---")
        for k, v in sorted(results.items(), key=lambda x: x[1], reverse=True):
            print(f"  {k}: {v:.2f}" if isinstance(v, float) else f"  {k}: {v}")
        return results

    # ==================== 数据处理 ====================

    def drop_duplicates(self, subset: list = None) -> "CsvAnalyzer":
        """去重"""
        seen = set()
        unique_rows = []
        for r in self.rows:
            key = tuple(r.get(col, "") for col in (subset or self.headers))
            if key not in seen:
                seen.add(key)
                unique_rows.append(r)
        removed = len(self.rows) - len(unique_rows)
        print(f"去重完成，移除 {removed} 条重复记录")
        return CsvAnalyzer.from_data(self.headers, unique_rows)

    def fill_na(self, column: str, fill_value):
        """填充空值"""
        count = 0
        for r in self.rows:
            if not r.get(column, "").strip():
                r[column] = str(fill_value)
                count += 1
        print(f"已填充 {count} 个空值")
        return self

    def add_column(self, name: str, func: callable):
        """添加计算列"""
        if name not in self.headers:
            self.headers.append(name)
        for r in self.rows:
            r[name] = str(func(r))
        print(f"已添加列: {name}")

    def rename_column(self, old_name: str, new_name: str):
        """重命名列"""
        if old_name in self.headers:
            idx = self.headers.index(old_name)
            self.headers[idx] = new_name
            for r in self.rows:
                if old_name in r:
                    r[new_name] = r.pop(old_name)
            print(f"列名 {old_name} -> {new_name}")

    def select(self, columns: list) -> "CsvAnalyzer":
        """选择指定列"""
        new_rows = [{c: r.get(c, "") for c in columns} for r in self.rows]
        return CsvAnalyzer.from_data(columns, new_rows)

    # ==================== 输出 ====================

    def display(self, rows: list = None, max_width: int = 20):
        """表格形式显示数据"""
        data = rows or self.rows
        if not data:
            print("  (无数据)")
            return

        cols = self.headers
        col_widths = {}
        for col in cols:
            max_len = max(len(str(col)), *(len(str(r.get(col, ""))) for r in data))
            col_widths[col] = min(max_len, max_width)

        # 表头
        header = " | ".join(str(col).ljust(col_widths[col]) for col in cols)
        sep = "-+-".join("-" * col_widths[col] for col in cols)
        print(header)
        print(sep)

        # 数据行
        for r in data[:50]:  # 最多显示 50 行
            row_str = " | ".join(
                str(r.get(col, ""))[:max_width].ljust(col_widths[col]) for col in cols
            )
            print(row_str)

        if len(data) > 50:
            print(f"  ... 共 {len(data)} 行，仅显示前 50 行")


def create_demo_csv(filepath: str):
    """创建演示 CSV 文件"""
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["姓名", "年龄", "城市", "薪资", "部门", "入职年份"])
        writer.writerow(["张三", "25", "北京", "15000", "技术部", "2020"])
        writer.writerow(["李四", "30", "上海", "20000", "市场部", "2018"])
        writer.writerow(["王五", "28", "北京", "18000", "技术部", "2019"])
        writer.writerow(["赵六", "35", "广州", "25000", "财务部", "2015"])
        writer.writerow(["钱七", "22", "上海", "12000", "市场部", "2022"])
        writer.writerow(["孙八", "32", "深圳", "22000", "技术部", "2017"])
        writer.writerow(["周九", "27", "北京", "16000", "人事部", "2021"])
        writer.writerow(["吴十", "29", "广州", "19000", "技术部", "2019"])
        writer.writerow(["郑十一", "26", "上海", "14000", "财务部", "2021"])
        writer.writerow(["王十二", "31", "深圳", "23000", "市场部", "2018"])
        writer.writerow(["张三", "25", "北京", "15000", "技术部", "2020"])  # 重复行
        writer.writerow(["刘十三", "", "杭州", "17000", "技术部", ""])  # 有空值


if __name__ == "__main__":
    # ===== 演示模式 =====
    print("=" * 60)
    print("  CSV 数据分析工具 Demo")
    print("=" * 60)

    demo_dir = os.path.dirname(__file__)
    demo_csv = os.path.join(demo_dir, "demo_data.csv")

    # 创建演示数据
    create_demo_csv(demo_csv)

    # 加载数据
    print("\n--- 1. 加载 CSV ---")
    analyzer = CsvAnalyzer(demo_csv)

    # 数据概览
    print("\n--- 2. 数据概览 ---")
    analyzer.info()

    # 预览数据
    print("\n--- 3. 前 5 行 ---")
    analyzer.display(analyzer.head())

    # 筛选
    print("\n--- 4. 筛选：城市=北京 ---")
    result = analyzer.filter_eq("城市", "北京")
    result.display()

    print("\n--- 5. 筛选：薪资 > 18000 ---")
    result = analyzer.filter_gt("薪资", 18000)
    result.display()

    print("\n--- 6. 筛选：部门包含'技术' ---")
    result = analyzer.filter_contains("部门", "技术")
    result.display()

    # 排序
    print("\n--- 7. 按薪资降序 ---")
    result = analyzer.sort_by("薪资", reverse=True)
    result.display()

    # 描述性统计
    print("\n--- 8. 描述性统计 ---")
    analyzer.describe()

    # 值统计
    print("\n--- 9. 城市分布 ---")
    analyzer.value_counts("城市")

    print("\n--- 10. 部门分布 ---")
    analyzer.value_counts("部门")

    # 分组聚合
    analyzer.group_aggregate("城市", "薪资", "mean")
    analyzer.group_aggregate("部门", "薪资", "mean")

    # 去重
    print("\n--- 11. 去重 ---")
    dedup = analyzer.drop_duplicates()
    dedup.display()

    # 填充空值
    print("\n--- 12. 填充空值 ---")
    analyzer.fill_na("年龄", "0")
    analyzer.fill_na("入职年份", "未知")

    # 添加计算列
    print("\n--- 13. 添加计算列 ---")
    analyzer.add_column(
        "年薪", lambda r: str(int(analyzer._to_float(r.get("薪资", 0)) or 0) * 12)
    )
    analyzer.display(analyzer.select(["姓名", "薪资", "年薪"]).rows)

    # 重命名列
    print("\n--- 14. 重命名列 ---")
    analyzer.rename_column("薪资", "月薪")

    # 保存
    output_csv = os.path.join(demo_dir, "analysis_result.csv")
    analyzer.save(output_csv)

    # 清理
    os.remove(demo_csv)
    os.remove(output_csv)

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
