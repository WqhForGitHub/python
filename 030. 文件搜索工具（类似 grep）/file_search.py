"""
文件搜索工具（类似 grep）
功能：在文件中搜索匹配的文本行，支持正则表达式、递归目录搜索、
      多文件搜索、上下文行显示、忽略大小写、反选、统计、高亮等
"""

import re
import os
import sys
from datetime import datetime


class FileSearcher:
    """文件搜索器"""

    # ANSI 颜色代码
    COLORS = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "bold": "\033[1m",
        "reset": "\033[0m",
    }

    def __init__(self):
        self.match_count = 0
        self.file_count = 0
        self.total_lines = 0

    def search(self, pattern: str, paths: list, **kwargs) -> list:
        """搜索入口
        pattern: 搜索模式（正则表达式或普通字符串）
        paths: 文件或目录路径列表
        kwargs:
            ignore_case: 忽略大小写 (bool)
            regex: 使用正则表达式 (bool)
            whole_word: 全词匹配 (bool)
            context: 上下文行数 (int)
            invert: 反选，显示不匹配的行 (bool)
            line_number: 显示行号 (bool)
            filename: 显示文件名 (bool)
            count_only: 仅统计匹配数 (bool)
            max_count: 最多显示多少条匹配 (int)
            include: 包含的文件模式 (list)
            exclude: 排除的文件模式 (list)
            color: 高亮匹配 (bool)
        """
        self.match_count = 0
        self.file_count = 0
        self.total_lines = 0

        ignore_case = kwargs.get("ignore_case", False)
        regex = kwargs.get("regex", True)
        whole_word = kwargs.get("whole_word", False)
        context = kwargs.get("context", 0)
        invert = kwargs.get("invert", False)
        line_number = kwargs.get("line_number", True)
        filename = kwargs.get("filename", True)
        count_only = kwargs.get("count_only", False)
        max_count = kwargs.get("max_count", None)
        include = kwargs.get("include", None)
        exclude = kwargs.get("exclude", None)
        color = kwargs.get("color", True)

        # 构建正则表达式
        search_pattern = pattern
        if not regex:
            search_pattern = re.escape(pattern)
        if whole_word:
            search_pattern = r"\b" + search_pattern + r"\b"

        flags = re.IGNORECASE if ignore_case else 0
        try:
            compiled = re.compile(search_pattern, flags)
        except re.error as e:
            print(f"正则表达式错误: {e}")
            return []

        # 收集文件
        files = self._collect_files(paths, include, exclude)

        results = []
        for filepath in files:
            file_results = self._search_file(
                filepath,
                compiled,
                context=context,
                invert=invert,
                line_number=line_number,
                filename=filename,
                count_only=count_only,
                max_count=max_count,
                color=color,
            )
            if file_results:
                self.file_count += 1
                results.extend(file_results)
                if max_count and self.match_count >= max_count:
                    break

        return results

    def _collect_files(
        self, paths: list, include: list = None, exclude: list = None
    ) -> list:
        """收集要搜索的文件"""
        files = []
        for path in paths:
            if os.path.isfile(path):
                files.append(path)
            elif os.path.isdir(path):
                for root, dirs, filenames in os.walk(path):
                    # 排除隐藏目录
                    dirs[:] = [d for d in dirs if not d.startswith(".")]

                    for fname in filenames:
                        filepath = os.path.join(root, fname)

                        # 包含过滤
                        if include:
                            if not any(fnmatch(fname, pat) for pat in include):
                                continue

                        # 排除过滤
                        if exclude:
                            if any(fnmatch(fname, pat) for pat in exclude):
                                continue

                        # 跳过二进制文件
                        if self._is_binary(filepath):
                            continue

                        files.append(filepath)
        return sorted(files)

    def _is_binary(self, filepath: str) -> bool:
        """判断是否为二进制文件"""
        try:
            with open(filepath, "rb") as f:
                chunk = f.read(8192)
                return b"\x00" in chunk
        except (IOError, OSError):
            return True

    def _search_file(self, filepath: str, pattern: re.Pattern, **kwargs) -> list:
        """搜索单个文件"""
        context = kwargs.get("context", 0)
        invert = kwargs.get("invert", False)
        line_number = kwargs.get("line_number", True)
        show_filename = kwargs.get("filename", True)
        count_only = kwargs.get("count_only", False)
        max_count = kwargs.get("max_count", None)
        color = kwargs.get("color", True)

        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except (IOError, OSError) as e:
            return [{"type": "error", "file": filepath, "message": str(e)}]

        results = []
        match_count_in_file = 0

        # 找到所有匹配行
        matched_lines = set()
        for i, line in enumerate(lines):
            is_match = bool(pattern.search(line.rstrip("\n")))
            if invert:
                is_match = not is_match
            if is_match:
                matched_lines.add(i)

        # 添加上下文行
        display_lines = set()
        for i in matched_lines:
            for j in range(max(0, i - context), min(len(lines), i + context + 1)):
                display_lines.add(j)

        if not matched_lines:
            return []

        if count_only:
            count = len(matched_lines)
            self.match_count += count
            prefix = f"{self._colorize(filepath, 'green')}: " if show_filename else ""
            results.append(
                {
                    "type": "count",
                    "file": filepath,
                    "count": count,
                    "display": f"{prefix}{count}",
                }
            )
            return results

        for i in sorted(display_lines):
            line = lines[i].rstrip("\n")
            is_match = i in matched_lines

            if is_match:
                self.match_count += 1
                match_count_in_file += 1
                if max_count and self.match_count > max_count:
                    break

            # 构建显示
            parts = []

            # 文件名
            if show_filename:
                file_display = self._colorize(filepath, "magenta")
                parts.append(file_display)

            # 行号
            if line_number:
                if is_match:
                    ln = self._colorize(str(i + 1), "green")
                else:
                    ln = self._colorize(str(i + 1), "cyan")
                parts.append(ln)

            # 行内容
            if is_match and not invert:
                content = self._highlight_matches(line, pattern, color)
            else:
                content = line
            parts.append(content)

            separator = (
                self._colorize(":", "bold") if is_match else self._colorize("-", "bold")
            )
            display = f" {separator} ".join(parts)

            results.append(
                {
                    "type": "match" if is_match else "context",
                    "file": filepath,
                    "line_number": i + 1,
                    "line": line,
                    "is_match": is_match,
                    "display": display,
                }
            )

        return results

    def _highlight_matches(self, text: str, pattern: re.Pattern, color: bool) -> str:
        """高亮匹配部分"""
        if not color:
            return text

        def replacer(match):
            return f"{self.COLORS['red']}{self.COLORS['bold']}{match.group()}{self.COLORS['reset']}"

        return pattern.sub(replacer, text)

    def _colorize(self, text: str, color: str) -> str:
        """给文本上色"""
        return f"{self.COLORS.get(color, '')}{text}{self.COLORS['reset']}"

    def print_results(self, results: list, verbose: bool = False):
        """打印搜索结果"""
        if not results:
            print("无匹配结果")
            return

        current_file = None
        for r in results:
            if r["type"] == "error":
                print(f"[错误] {r['file']}: {r['message']}")
                continue
            if r["type"] == "count":
                print(r["display"])
                continue

            # 文件分隔
            if verbose and r["file"] != current_file:
                current_file = r["file"]
                print(f"\n{'=' * 60}")
                print(f"文件: {r['file']}")
                print(f"{'=' * 60}")

            print(r["display"])

    def print_summary(self):
        """打印搜索摘要"""
        print(f"\n--- 搜索摘要 ---")
        print(f"匹配文件数: {self.file_count}")
        print(f"匹配行数:   {self.match_count}")


def fnmatch(name: str, pattern: str) -> bool:
    """简单的文件名匹配（支持 * 和 ?）"""
    regex = pattern.replace(".", r"\.").replace("*", ".*").replace("?", ".")
    return bool(re.fullmatch(regex, name, re.IGNORECASE))


# ==================== 命令行接口 ====================


def create_demo_files(demo_dir: str):
    """创建演示文件"""
    os.makedirs(os.path.join(demo_dir, "src"), exist_ok=True)
    os.makedirs(os.path.join(demo_dir, "docs"), exist_ok=True)

    # Python 文件
    with open(os.path.join(demo_dir, "src", "main.py"), "w", encoding="utf-8") as f:
        f.write('''"""主程序入口"""
import os
import sys

def hello():
    """打印欢迎信息"""
    print("Hello, World!")
    return True

def goodbye():
    """打印告别信息"""
    print("Goodbye!")
    return False

class Application:
    def __init__(self, name):
        self.name = name
        self.running = False

    def start(self):
        self.running = True
        print(f"Application {self.name} started")

    def stop(self):
        self.running = False
        print(f"Application {self.name} stopped")

if __name__ == "__main__":
    app = Application("Demo")
    app.start()
    hello()
    app.stop()
''')

    with open(os.path.join(demo_dir, "src", "utils.py"), "w", encoding="utf-8") as f:
        f.write('''"""工具函数"""
import re
from datetime import datetime

def read_file(filepath):
    """读取文件内容"""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def write_file(filepath, content):
    """写入文件"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

def get_timestamp():
    """获取当前时间戳"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def find_pattern(text, pattern):
    """在文本中查找模式"""
    return re.findall(pattern, text)
''')

    # Markdown 文件
    with open(os.path.join(demo_dir, "docs", "README.md"), "w", encoding="utf-8") as f:
        f.write("""# 项目说明

这是一个演示项目。

## 功能

- 文件搜索
- 模式匹配
- 结果高亮

## 使用方法

```bash
python file_search.py "pattern" /path/to/search
```

## 作者

张三 - 2024
""")

    # 配置文件
    with open(os.path.join(demo_dir, "config.txt"), "w", encoding="utf-8") as f:
        f.write("""# 应用配置
app_name = DemoApp
version = 1.0.0
debug = True
host = localhost
port = 8080

# 数据库配置
db_host = localhost
db_port = 3306
db_name = demo_db
db_user = admin
""")

    # 日志文件
    with open(os.path.join(demo_dir, "app.log"), "w", encoding="utf-8") as f:
        f.write("""[2024-01-15 10:00:01] INFO  - Application started
[2024-01-15 10:00:02] INFO  - Loading configuration
[2024-01-15 10:00:03] ERROR - Failed to connect to database
[2024-01-15 10:00:04] WARN  - Retrying connection...
[2024-01-15 10:00:05] INFO  - Database connected successfully
[2024-01-15 10:00:06] INFO  - Server running on localhost:8080
[2024-01-15 10:01:00] ERROR - Request timeout for /api/data
[2024-01-15 10:01:01] INFO  - Request processed successfully
[2024-01-15 10:05:00] ERROR - Memory usage exceeded threshold
[2024-01-15 10:05:01] WARN  - Clearing cache
""")


def cleanup_demo_files(demo_dir: str):
    """清理演示文件"""
    import shutil

    src_dir = os.path.join(demo_dir, "src")
    docs_dir = os.path.join(demo_dir, "docs")
    if os.path.exists(src_dir):
        shutil.rmtree(src_dir)
    if os.path.exists(docs_dir):
        shutil.rmtree(docs_dir)
    for f in ["config.txt", "app.log"]:
        fp = os.path.join(demo_dir, f)
        if os.path.exists(fp):
            os.remove(fp)


if __name__ == "__main__":
    # ===== 演示模式 =====
    print("=" * 60)
    print("  文件搜索工具（类似 grep）Demo")
    print("=" * 60)

    demo_dir = os.path.dirname(__file__)
    create_demo_files(demo_dir)

    searcher = FileSearcher()

    # 1. 基本搜索
    print("\n--- 1. 搜索 'def ' (函数定义) ---")
    results = searcher.search(
        r"def\s+\w+",
        [os.path.join(demo_dir, "src")],
        regex=True,
        color=False,
        filename=True,
    )
    searcher.print_results(results)
    searcher.print_summary()

    # 2. 忽略大小写搜索
    print("\n--- 2. 搜索 'error' (忽略大小写) ---")
    results = searcher.search(
        "error", [os.path.join(demo_dir, "app.log")], ignore_case=True, color=False
    )
    searcher.print_results(results)
    searcher.print_summary()

    # 3. 带上下文搜索
    print("\n--- 3. 搜索 'ERROR' (上下文 1 行) ---")
    results = searcher.search(
        "ERROR", [os.path.join(demo_dir, "app.log")], context=1, color=False
    )
    searcher.print_results(results)
    searcher.print_summary()

    # 4. 全词匹配
    print("\n--- 4. 搜索 'Application' (全词匹配) ---")
    results = searcher.search(
        "Application",
        [os.path.join(demo_dir, "src"), os.path.join(demo_dir, "app.log")],
        whole_word=True,
        color=False,
    )
    searcher.print_results(results)
    searcher.print_summary()

    # 5. 递归目录搜索
    print("\n--- 5. 递归搜索 'localhost' ---")
    results = searcher.search(
        "localhost",
        [demo_dir],
        include=["*.py", "*.txt", "*.log"],
        exclude=["*.md"],
        color=False,
    )
    searcher.print_results(results)
    searcher.print_summary()

    # 6. 仅统计
    print("\n--- 6. 统计每个文件的匹配数 ---")
    results = searcher.search(
        r"\b\w+\b", [os.path.join(demo_dir, "src")], count_only=True, color=False
    )
    searcher.print_results(results)
    searcher.print_summary()

    # 7. 反选
    print("\n--- 7. 日志中非 INFO 的行 ---")
    results = searcher.search(
        "INFO", [os.path.join(demo_dir, "app.log")], invert=True, color=False
    )
    searcher.print_results(results)
    searcher.print_summary()

    # 8. 正则高级搜索
    print("\n--- 8. 搜索 IP/端口格式 (\\d+:\\d+) ---")
    results = searcher.search(
        r"\d+:\d+", [demo_dir], include=["*.txt", "*.log"], color=False
    )
    searcher.print_results(results)
    searcher.print_summary()

    # 9. 搜索 print 语句
    print("\n--- 9. 搜索所有 print 语句 ---")
    results = searcher.search(
        r"print\s*\(", [os.path.join(demo_dir, "src")], color=False
    )
    searcher.print_results(results)
    searcher.print_summary()

    # 10. 搜索类定义
    print("\n--- 10. 搜索类定义 ---")
    results = searcher.search(
        r"class\s+\w+", [os.path.join(demo_dir, "src")], color=False
    )
    searcher.print_results(results)
    searcher.print_summary()

    # 清理
    cleanup_demo_files(demo_dir)

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)

    # ===== 命令行用法 =====
    # python file_search.py "pattern" path1 path2 [options]
    # 选项:
    #   -i, --ignore-case    忽略大小写
    #   -w, --whole-word     全词匹配
    #   -F, --fixed-string   固定字符串（非正则）
    #   -c, --count          仅统计匹配数
    #   -v, --invert-match   反选
    #   -C NUM, --context    上下文行数
    #   --include PAT        包含的文件模式
    #   --exclude PAT        排除的文件模式
    #   --no-color           禁用颜色
    #   -n, --line-number    显示行号
    #   -m NUM, --max-count  最多显示 NUM 条匹配
