"""
简单日志系统
支持多级别日志（DEBUG/INFO/WARNING/ERROR/CRITICAL），
日志可输出到控制台和文件，支持按时间/级别过滤查看。
"""

import os
import sys
from datetime import datetime

# ── 日志级别定义 ──────────────────────────────────────────

LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}

LEVEL_COLORS = {
    "DEBUG": "\033[36m",  # 青色
    "INFO": "\033[32m",  # 绿色
    "WARNING": "\033[33m",  # 黄色
    "ERROR": "\033[31m",  # 红色
    "CRITICAL": "\033[35m",  # 紫色
}

RESET = "\033[0m"

# ── 日志记录器 ────────────────────────────────────────────


class SimpleLogger:
    """简单的日志记录器。"""

    def __init__(
        self, name: str = "app", log_file: str | None = None, level: str = "DEBUG"
    ):
        self.name = name
        self.log_file = log_file
        self.level = LEVELS.get(level.upper(), 10)
        self.records: list[dict] = []
        self._console = True

    def _log(self, level: str, message: str) -> None:
        """核心日志方法。"""
        if LEVELS.get(level, 0) < self.level:
            return

        now = datetime.now()
        record = {
            "time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "level": level,
            "name": self.name,
            "message": message,
        }
        self.records.append(record)

        # 控制台输出（带颜色）
        if self._console:
            color = LEVEL_COLORS.get(level, "")
            print(
                f"  {color}[{record['time']}] [{level:<8s}] [{self.name}] {message}{RESET}"
            )

        # 文件输出
        if self.log_file:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(f"[{record['time']}] [{level}] [{self.name}] {message}\n")
            except Exception as e:
                print(f"  写入日志文件失败: {e}")

    def debug(self, msg: str) -> None:
        self._log("DEBUG", msg)

    def info(self, msg: str) -> None:
        self._log("INFO", msg)

    def warning(self, msg: str) -> None:
        self._log("WARNING", msg)

    def error(self, msg: str) -> None:
        self._log("ERROR", msg)

    def critical(self, msg: str) -> None:
        self._log("CRITICAL", msg)

    def set_level(self, level: str) -> None:
        """设置日志级别。"""
        if level.upper() in LEVELS:
            self.level = LEVELS[level.upper()]
            print(f"  日志级别已设为 {level.upper()}")
        else:
            print(f"  无效级别，可选: {', '.join(LEVELS.keys())}")

    def set_log_file(self, path: str) -> None:
        """设置日志文件路径。"""
        self.log_file = path
        print(f"  日志文件已设为: {path}")

    def query(
        self,
        level: str | None = None,
        start: str | None = None,
        end: str | None = None,
        keyword: str | None = None,
    ) -> list[dict]:
        """按条件查询日志记录。"""
        results = self.records
        if level:
            level_val = LEVELS.get(level.upper(), 0)
            results = [r for r in results if LEVELS.get(r["level"], 0) >= level_val]
        if start:
            results = [r for r in results if r["time"] >= start]
        if end:
            results = [r for r in results if r["time"] <= end]
        if keyword:
            results = [r for r in results if keyword.lower() in r["message"].lower()]
        return results

    def show_records(self, records: list[dict] | None = None) -> None:
        """展示日志记录。"""
        items = records if records is not None else self.records
        if not items:
            print("  暂无日志记录")
            return
        print(f"\n  共 {len(items)} 条日志：")
        for r in items[-50:]:  # 最多显示最近50条
            color = LEVEL_COLORS.get(r["level"], "")
            print(f"  {color}[{r['time']}] [{r['level']:<8s}] {r['message']}{RESET}")
        print()

    def clear(self) -> None:
        """清空内存中的日志记录。"""
        self.records.clear()
        print("  日志已清空")

    def export(self, path: str) -> None:
        """导出日志到文件。"""
        try:
            with open(path, "w", encoding="utf-8") as f:
                for r in self.records:
                    f.write(
                        f"[{r['time']}] [{r['level']}] [{r['name']}] {r['message']}\n"
                    )
            print(f"  已导出 {len(self.records)} 条日志到 {path}")
        except Exception as e:
            print(f"  导出失败: {e}")


# ── 主菜单 ────────────────────────────────────────────────


def print_menu() -> None:
    print("=" * 45)
    print("  简单日志系统")
    print("=" * 45)
    print("  1. 记录 DEBUG 日志")
    print("  2. 记录 INFO 日志")
    print("  3. 记录 WARNING 日志")
    print("  4. 记录 ERROR 日志")
    print("  5. 记录 CRITICAL 日志")
    print("  6. 查看所有日志")
    print("  7. 按级别查询日志")
    print("  8. 按关键词搜索日志")
    print("  9. 设置日志级别")
    print("  10. 设置日志文件")
    print("  11. 导出日志")
    print("  12. 清空日志")
    print("  13. 模拟日志生成")
    print("  q. 退出")
    print("-" * 45)


def main() -> None:
    logger = SimpleLogger("demo")

    while True:
        print_menu()
        choice = input("  请选择: ").strip()

        if choice == "q":
            print("  再见！")
            break

        elif choice in ("1", "2", "3", "4", "5"):
            level_map = {
                "1": "debug",
                "2": "info",
                "3": "warning",
                "4": "error",
                "5": "critical",
            }
            msg = input("  输入日志内容: ").strip()
            if msg:
                getattr(logger, level_map[choice])(msg)
            else:
                print("  日志内容不能为空")

        elif choice == "6":
            logger.show_records()

        elif choice == "7":
            level = input("  最低级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）: ").strip()
            results = logger.query(level=level)
            logger.show_records(results)

        elif choice == "8":
            keyword = input("  搜索关键词: ").strip()
            if keyword:
                results = logger.query(keyword=keyword)
                logger.show_records(results)

        elif choice == "9":
            level = input("  日志级别: ").strip()
            logger.set_level(level)

        elif choice == "10":
            path = input("  日志文件路径: ").strip()
            if path:
                logger.set_log_file(path)

        elif choice == "11":
            path = input("  导出路径: ").strip()
            if path:
                logger.export(path)

        elif choice == "12":
            logger.clear()

        elif choice == "13":
            import random

            sample_msgs = {
                "DEBUG": ["变量 x = 42", "函数调用完成", "缓存命中"],
                "INFO": ["用户登录成功", "服务启动完成", "数据同步完成"],
                "WARNING": [
                    "磁盘空间不足 80%",
                    "响应时间超过阈值",
                    "配置项缺失，使用默认值",
                ],
                "ERROR": ["数据库连接失败", "文件读取错误", "请求超时"],
                "CRITICAL": ["系统内存耗尽", "主服务崩溃", "数据损坏"],
            }
            level = random.choice(list(sample_msgs.keys()))
            msg = random.choice(sample_msgs[level])
            getattr(logger, level.lower())(msg)

        else:
            print("  无效选择，请重新输入")


if __name__ == "__main__":
    main()
