"""
日志分析器
功能：
    - 解析常见格式的日志（如 [时间] 级别 - 消息）
    - 按日志级别、时间段、关键字过滤
    - 统计各级别数量、Top N 错误信息、IP/路径访问频次
    - 检测异常突增、生成报告
"""

import re
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta


class LogAnalyzer:
    """日志分析器"""

    # 常见日志格式：[2024-01-15 10:00:01] INFO  - message
    LOG_PATTERN = re.compile(
        r"\[(?P<time>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})\]\s+"
        r"(?P<level>[A-Z]+)\s*-\s*(?P<message>.*)"
    )

    # 通用 IP 匹配
    IP_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

    # URL/路径匹配
    PATH_PATTERN = re.compile(r"(?:GET|POST|PUT|DELETE)\s+(\S+)|(/[\w/\-\.]+)")

    LEVELS = ["DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL", "FATAL"]

    def __init__(self):
        self.entries = []
        self.parse_errors = 0

    def load(self, filepath: str):
        """加载日志文件"""
        if not os.path.isfile(filepath):
            raise FileNotFoundError(filepath)

        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for lineno, line in enumerate(f, 1):
                line = line.rstrip("\n")
                if not line.strip():
                    continue
                m = self.LOG_PATTERN.match(line)
                if m:
                    try:
                        ts = datetime.strptime(
                            m.group("time").replace("T", " "), "%Y-%m-%d %H:%M:%S"
                        )
                    except ValueError:
                        ts = None
                    self.entries.append(
                        {
                            "lineno": lineno,
                            "time": ts,
                            "level": m.group("level").upper(),
                            "message": m.group("message"),
                            "raw": line,
                        }
                    )
                else:
                    self.parse_errors += 1
                    self.entries.append(
                        {
                            "lineno": lineno,
                            "time": None,
                            "level": "UNKNOWN",
                            "message": line,
                            "raw": line,
                        }
                    )

    def filter(self, level=None, keyword=None, start=None, end=None):
        """过滤日志条目"""
        result = []
        for e in self.entries:
            if level and e["level"] != level.upper():
                continue
            if keyword and keyword.lower() not in e["message"].lower():
                continue
            if start and e["time"] and e["time"] < start:
                continue
            if end and e["time"] and e["time"] > end:
                continue
            result.append(e)
        return result

    def count_by_level(self):
        """统计各日志级别数量"""
        return Counter(e["level"] for e in self.entries)

    def count_by_hour(self):
        """按小时统计"""
        c = Counter()
        for e in self.entries:
            if e["time"]:
                key = e["time"].strftime("%Y-%m-%d %H:00")
                c[key] += 1
        return c

    def top_errors(self, n=5):
        """Top N 错误消息（同类合并）"""
        errors = [
            self._normalize(e["message"]) for e in self.entries if e["level"] == "ERROR"
        ]
        return Counter(errors).most_common(n)

    def top_ips(self, n=5):
        """Top N IP"""
        ips = []
        for e in self.entries:
            ips.extend(self.IP_PATTERN.findall(e["raw"]))
        return Counter(ips).most_common(n)

    def top_paths(self, n=5):
        """Top N 路径"""
        paths = []
        for e in self.entries:
            for m in self.PATH_PATTERN.finditer(e["raw"]):
                p = m.group(1) or m.group(2)
                if p:
                    paths.append(p)
        return Counter(paths).most_common(n)

    def detect_spikes(self, window_minutes=1, threshold=3):
        """检测突增（每窗口错误数超过阈值）"""
        bucket = defaultdict(int)
        for e in self.entries:
            if e["level"] == "ERROR" and e["time"]:
                key = e["time"].replace(
                    second=0,
                    minute=(e["time"].minute // window_minutes) * window_minutes,
                )
                bucket[key] += 1
        return [(k, v) for k, v in sorted(bucket.items()) if v >= threshold]

    def time_range(self):
        """日志时间范围"""
        times = [e["time"] for e in self.entries if e["time"]]
        if not times:
            return None, None
        return min(times), max(times)

    def _normalize(self, msg: str) -> str:
        """归一化错误消息（去除变量数字、路径）"""
        msg = re.sub(r"\d+", "N", msg)
        msg = re.sub(r"\s+", " ", msg).strip()
        if len(msg) > 80:
            msg = msg[:77] + "..."
        return msg

    def report(self):
        """生成分析报告字符串"""
        lines = []
        lines.append("=" * 60)
        lines.append("  日志分析报告")
        lines.append("=" * 60)
        lines.append(f"总条数:       {len(self.entries)}")
        lines.append(f"解析失败行数: {self.parse_errors}")

        start, end = self.time_range()
        if start and end:
            lines.append(f"时间范围:     {start} ~ {end}")

        lines.append("\n[级别分布]")
        for lvl, cnt in self.count_by_level().most_common():
            lines.append(f"  {lvl:<10} {cnt}")

        lines.append("\n[每小时分布]")
        for hr, cnt in sorted(self.count_by_hour().items()):
            bar = "#" * min(cnt, 40)
            lines.append(f"  {hr}  {cnt:4d} {bar}")

        lines.append("\n[Top 5 错误消息]")
        for msg, cnt in self.top_errors(5):
            lines.append(f"  ({cnt}) {msg}")

        ips = self.top_ips(5)
        if ips:
            lines.append("\n[Top 5 IP]")
            for ip, cnt in ips:
                lines.append(f"  {ip:<20} {cnt}")

        paths = self.top_paths(5)
        if paths:
            lines.append("\n[Top 5 路径]")
            for p, cnt in paths:
                lines.append(f"  {p:<30} {cnt}")

        spikes = self.detect_spikes(window_minutes=1, threshold=2)
        if spikes:
            lines.append("\n[错误突增窗口 (>=2)]")
            for t, cnt in spikes:
                lines.append(f"  {t}  {cnt} 次")

        return "\n".join(lines)


# ==================== Demo ====================


def create_demo_log(path: str):
    sample = """[2024-01-15 10:00:01] INFO  - Application started
[2024-01-15 10:00:02] INFO  - Loading configuration from /etc/app.conf
[2024-01-15 10:00:03] ERROR - Failed to connect to database 192.168.1.10
[2024-01-15 10:00:04] WARN  - Retrying connection...
[2024-01-15 10:00:05] INFO  - Database connected successfully
[2024-01-15 10:00:06] INFO  - Server running on localhost:8080
[2024-01-15 10:01:00] INFO  - GET /api/users 200 from 10.0.0.5
[2024-01-15 10:01:01] INFO  - GET /api/users 200 from 10.0.0.6
[2024-01-15 10:01:02] ERROR - Request timeout for /api/data from 10.0.0.7
[2024-01-15 10:01:03] ERROR - Request timeout for /api/data from 10.0.0.8
[2024-01-15 10:01:04] ERROR - Request timeout for /api/data from 10.0.0.9
[2024-01-15 10:02:00] INFO  - POST /api/login 200 from 10.0.0.5
[2024-01-15 10:05:00] ERROR - Memory usage exceeded threshold 95%
[2024-01-15 10:05:01] WARN  - Clearing cache
[2024-01-15 10:05:02] INFO  - Cache cleared
[2024-01-15 11:00:00] INFO  - GET /api/users 200 from 10.0.0.5
[2024-01-15 11:00:30] ERROR - Failed to connect to database 192.168.1.10
[2024-01-15 11:01:00] INFO  - Heartbeat OK
[2024-01-15 12:00:00] CRITICAL - Disk full on /var/log
this is a malformed line without timestamp
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(sample)


if __name__ == "__main__":
    demo_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(demo_dir, "demo_app.log")

    print("=" * 60)
    print("  日志分析器 Demo")
    print("=" * 60)

    create_demo_log(log_file)

    analyzer = LogAnalyzer()
    analyzer.load(log_file)

    # 1. 完整报告
    print(analyzer.report())

    # 2. 过滤示例
    print("\n--- 仅查看 ERROR 级别 ---")
    for e in analyzer.filter(level="ERROR"):
        print(f"  L{e['lineno']:3d}  {e['time']}  {e['message']}")

    # 3. 关键字过滤
    print("\n--- 包含 'database' 关键字 ---")
    for e in analyzer.filter(keyword="database"):
        print(f"  L{e['lineno']:3d}  [{e['level']}]  {e['message']}")

    # 4. 时间段过滤
    print("\n--- 时间段 10:00 ~ 10:02 ---")
    start = datetime(2024, 1, 15, 10, 0, 0)
    end = datetime(2024, 1, 15, 10, 2, 0)
    for e in analyzer.filter(start=start, end=end):
        print(f"  {e['time']}  [{e['level']:<5}]  {e['message']}")

    # 清理
    if os.path.exists(log_file):
        os.remove(log_file)

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
