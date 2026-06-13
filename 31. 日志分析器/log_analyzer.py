"""
日志分析器
功能：解析常见格式的日志文件，统计日志级别分布、TOP IP/URL、错误聚合、
      时间段分布、慢请求统计、异常追踪等
"""

import re
import os
from collections import Counter, defaultdict
from datetime import datetime


class LogAnalyzer:
    """日志分析器"""

    # 常见日志级别
    LOG_LEVELS = ["DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL", "FATAL"]

    # 应用日志正则: [2024-01-15 10:00:01] INFO  - message
    APP_LOG_PATTERN = re.compile(
        r"\[(?P<time>\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})\]\s+"
        r"(?P<level>DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL)\s*-?\s*"
        r"(?P<message>.*)"
    )

    # Nginx/Apache 访问日志: 127.0.0.1 - - [10/Oct/2024:13:55:36 +0000] "GET /index HTTP/1.1" 200 1234
    ACCESS_LOG_PATTERN = re.compile(
        r"(?P<ip>\d+\.\d+\.\d+\.\d+)\s+\S+\s+\S+\s+"
        r"\[(?P<time>[^\]]+)\]\s+"
        r'"(?P<method>\w+)\s+(?P<url>\S+)\s+(?P<protocol>[^"]+)"\s+'
        r"(?P<status>\d{3})\s+(?P<size>\d+|-)"
        r'(?:\s+"(?P<referer>[^"]*)"\s+"(?P<agent>[^"]*)")?'
        r"(?:\s+(?P<latency>\d+(?:\.\d+)?))?"
    )

    def __init__(self):
        self.reset()

    def reset(self):
        """重置统计数据"""
        self.total_lines = 0
        self.parsed_lines = 0
        self.unparsed_lines = 0
        self.level_counter = Counter()
        self.ip_counter = Counter()
        self.url_counter = Counter()
        self.status_counter = Counter()
        self.method_counter = Counter()
        self.hour_counter = Counter()
        self.error_messages = Counter()
        self.slow_requests = []
        self.first_time = None
        self.last_time = None

    def analyze_file(self, filepath: str, log_type: str = "auto") -> dict:
        """分析日志文件"""
        self.reset()

        if not os.path.exists(filepath):
            return {"error": f"文件不存在: {filepath}"}

        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    self.total_lines += 1
                    line = line.strip()
                    if not line:
                        continue
                    self._parse_line(line, log_type)
        except (IOError, OSError) as e:
            return {"error": str(e)}

        return self.summary()

    def _parse_line(self, line: str, log_type: str):
        """解析单行日志"""
        if log_type == "app" or log_type == "auto":
            m = self.APP_LOG_PATTERN.match(line)
            if m:
                self._handle_app_log(m)
                return

        if log_type == "access" or log_type == "auto":
            m = self.ACCESS_LOG_PATTERN.match(line)
            if m:
                self._handle_access_log(m)
                return

        self.unparsed_lines += 1

    def _handle_app_log(self, m: re.Match):
        """处理应用日志"""
        self.parsed_lines += 1
        level = m.group("level").upper()
        if level == "WARNING":
            level = "WARN"
        self.level_counter[level] += 1

        time_str = m.group("time")
        try:
            t = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            self._update_time_range(t)
            self.hour_counter[t.strftime("%Y-%m-%d %H")] += 1
        except ValueError:
            pass

        if level in ("ERROR", "CRITICAL", "FATAL"):
            msg = m.group("message").strip()
            # 归一化错误消息（去除数字 ID 等）
            normalized = re.sub(r"\d+", "N", msg)
            normalized = re.sub(r"\s+", " ", normalized)[:200]
            self.error_messages[normalized] += 1

    def _handle_access_log(self, m: re.Match):
        """处理访问日志"""
        self.parsed_lines += 1
        self.ip_counter[m.group("ip")] += 1
        self.url_counter[m.group("url")] += 1
        self.method_counter[m.group("method")] += 1

        status = m.group("status")
        self.status_counter[status] += 1

        # 时间解析
        time_str = m.group("time")
        try:
            t = datetime.strptime(time_str.split()[0], "%d/%b/%Y:%H:%M:%S")
            self._update_time_range(t)
            self.hour_counter[t.strftime("%Y-%m-%d %H")] += 1
        except (ValueError, IndexError):
            pass

        # 慢请求
        latency = m.group("latency")
        if latency:
            try:
                lat = float(latency)
                if lat > 1.0:  # 大于 1 秒视为慢请求
                    self.slow_requests.append(
                        {
                            "url": m.group("url"),
                            "latency": lat,
                            "status": status,
                            "ip": m.group("ip"),
                        }
                    )
            except ValueError:
                pass

    def _update_time_range(self, t: datetime):
        """更新时间范围"""
        if self.first_time is None or t < self.first_time:
            self.first_time = t
        if self.last_time is None or t > self.last_time:
            self.last_time = t

    def summary(self, top_n: int = 10) -> dict:
        """生成统计摘要"""
        # 按延迟排序慢请求
        slow_sorted = sorted(self.slow_requests, key=lambda x: -x["latency"])[:top_n]

        return {
            "total_lines": self.total_lines,
            "parsed_lines": self.parsed_lines,
            "unparsed_lines": self.unparsed_lines,
            "time_range": {
                "first": self.first_time.isoformat() if self.first_time else None,
                "last": self.last_time.isoformat() if self.last_time else None,
            },
            "levels": dict(self.level_counter),
            "top_ips": self.ip_counter.most_common(top_n),
            "top_urls": self.url_counter.most_common(top_n),
            "status_codes": dict(self.status_counter),
            "methods": dict(self.method_counter),
            "hours": dict(self.hour_counter),
            "top_errors": self.error_messages.most_common(top_n),
            "slow_requests": slow_sorted,
        }

    def print_report(self, summary: dict):
        """打印分析报告"""
        if "error" in summary:
            print(f"分析失败: {summary['error']}")
            return

        print(f"\n{'=' * 60}")
        print("  日志分析报告")
        print(f"{'=' * 60}")
        print(f"总行数:     {summary['total_lines']}")
        print(f"已解析:     {summary['parsed_lines']}")
        print(f"未解析:     {summary['unparsed_lines']}")

        tr = summary["time_range"]
        if tr["first"]:
            print(f"时间范围:   {tr['first']}  ~  {tr['last']}")

        if summary["levels"]:
            print("\n--- 日志级别分布 ---")
            for level in ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL", "FATAL"]:
                if level in summary["levels"]:
                    cnt = summary["levels"][level]
                    bar = "#" * min(50, cnt)
                    print(f"  {level:10s} {cnt:6d}  {bar}")

        if summary["status_codes"]:
            print("\n--- HTTP 状态码 ---")
            for code, cnt in sorted(summary["status_codes"].items()):
                print(f"  {code}: {cnt}")

        if summary["methods"]:
            print("\n--- HTTP 方法 ---")
            for method, cnt in summary["methods"].items():
                print(f"  {method}: {cnt}")

        if summary["top_ips"]:
            print("\n--- TOP IP ---")
            for ip, cnt in summary["top_ips"]:
                print(f"  {ip:20s} {cnt}")

        if summary["top_urls"]:
            print("\n--- TOP URL ---")
            for url, cnt in summary["top_urls"]:
                print(f"  {url:40s} {cnt}")

        if summary["top_errors"]:
            print("\n--- TOP 错误消息 ---")
            for msg, cnt in summary["top_errors"]:
                print(f"  [{cnt}x] {msg[:80]}")

        if summary["slow_requests"]:
            print("\n--- 慢请求 (>1s) ---")
            for req in summary["slow_requests"]:
                print(
                    f"  {req['latency']:6.2f}s  {req['status']}  "
                    f"{req['ip']:15s}  {req['url']}"
                )

        if summary["hours"]:
            print("\n--- 按小时分布 ---")
            for hour, cnt in sorted(summary["hours"].items()):
                bar = "#" * min(40, cnt)
                print(f"  {hour}  {cnt:6d}  {bar}")


# ==================== 演示 ====================


def create_demo_logs(demo_dir: str):
    """创建示例日志文件"""
    # 应用日志
    app_log = os.path.join(demo_dir, "app.log")
    with open(app_log, "w", encoding="utf-8") as f:
        f.write(
            """[2024-01-15 09:00:01] INFO  - Application started
[2024-01-15 09:00:02] INFO  - Loading configuration from config.yaml
[2024-01-15 09:00:03] DEBUG - Config loaded: {host: localhost, port: 8080}
[2024-01-15 09:00:05] INFO  - Connected to database
[2024-01-15 09:01:10] WARN  - High memory usage: 78%
[2024-01-15 09:05:22] ERROR - Failed to process request id=12345
[2024-01-15 09:05:23] ERROR - Failed to process request id=12346
[2024-01-15 09:05:24] ERROR - Failed to process request id=12347
[2024-01-15 09:10:00] INFO  - Cleaning cache
[2024-01-15 10:00:01] ERROR - Database connection lost
[2024-01-15 10:00:05] WARN  - Reconnecting to database (attempt 1)
[2024-01-15 10:00:10] WARN  - Reconnecting to database (attempt 2)
[2024-01-15 10:00:15] INFO  - Database reconnected
[2024-01-15 10:30:00] CRITICAL - Disk space below 5%
[2024-01-15 11:00:00] ERROR - Out of memory error
[2024-01-15 11:15:00] INFO  - GC triggered
[2024-01-15 11:30:00] INFO  - Memory normalized
[2024-01-15 12:00:00] WARNING - Slow query detected (3.2s)
[2024-01-15 13:00:00] DEBUG - Heartbeat
[2024-01-15 14:00:00] INFO  - User login: alice
[2024-01-15 14:05:00] INFO  - User login: bob
[2024-01-15 14:10:00] ERROR - Authentication failed for user: charlie
"""
        )

    # 访问日志（Nginx 风格）
    access_log = os.path.join(demo_dir, "access.log")
    with open(access_log, "w", encoding="utf-8") as f:
        f.write(
            '''192.168.1.10 - - [15/Jan/2024:09:00:01 +0000] "GET /index.html HTTP/1.1" 200 2326 "-" "Mozilla/5.0" 0.123
192.168.1.10 - - [15/Jan/2024:09:00:05 +0000] "GET /api/users HTTP/1.1" 200 4521 "-" "Mozilla/5.0" 0.234
192.168.1.20 - - [15/Jan/2024:09:01:10 +0000] "POST /api/login HTTP/1.1" 200 156 "-" "curl/7.68" 0.456
192.168.1.30 - - [15/Jan/2024:09:02:00 +0000] "GET /api/products HTTP/1.1" 500 234 "-" "Mozilla/5.0" 1.234
192.168.1.30 - - [15/Jan/2024:09:02:30 +0000] "GET /api/products HTTP/1.1" 500 234 "-" "Mozilla/5.0" 2.567
192.168.1.10 - - [15/Jan/2024:09:05:00 +0000] "GET /static/app.js HTTP/1.1" 200 12456 "-" "Mozilla/5.0" 0.045
192.168.1.40 - - [15/Jan/2024:09:10:00 +0000] "GET /admin HTTP/1.1" 403 89 "-" "Mozilla/5.0" 0.012
192.168.1.40 - - [15/Jan/2024:09:10:05 +0000] "GET /admin HTTP/1.1" 403 89 "-" "Mozilla/5.0" 0.011
192.168.1.40 - - [15/Jan/2024:09:10:10 +0000] "GET /admin HTTP/1.1" 403 89 "-" "Mozilla/5.0" 0.013
10.0.0.5 - - [15/Jan/2024:10:00:00 +0000] "GET /api/data HTTP/1.1" 200 8945 "-" "PostmanRuntime" 3.456
10.0.0.5 - - [15/Jan/2024:10:01:00 +0000] "GET /api/data HTTP/1.1" 200 8945 "-" "PostmanRuntime" 0.234
10.0.0.5 - - [15/Jan/2024:10:02:00 +0000] "POST /api/upload HTTP/1.1" 200 156 "-" "PostmanRuntime" 5.678
192.168.1.10 - - [15/Jan/2024:11:00:00 +0000] "GET /index.html HTTP/1.1" 200 2326 "-" "Mozilla/5.0" 0.089
192.168.1.10 - - [15/Jan/2024:11:00:30 +0000] "GET /404page HTTP/1.1" 404 156 "-" "Mozilla/5.0" 0.034
192.168.1.50 - - [15/Jan/2024:14:00:00 +0000] "GET /api/users HTTP/1.1" 200 4521 "-" "Mozilla/5.0" 0.112
192.168.1.50 - - [15/Jan/2024:14:05:00 +0000] "DELETE /api/users/100 HTTP/1.1" 204 0 "-" "Mozilla/5.0" 0.156
192.168.1.50 - - [15/Jan/2024:14:10:00 +0000] "PUT /api/users/100 HTTP/1.1" 200 234 "-" "Mozilla/5.0" 0.198
'''
        )

    return app_log, access_log


def cleanup_demo_logs(demo_dir: str):
    """清理示例日志"""
    for fname in ["app.log", "access.log"]:
        fp = os.path.join(demo_dir, fname)
        if os.path.exists(fp):
            os.remove(fp)


if __name__ == "__main__":
    print("=" * 60)
    print("  日志分析器 Demo")
    print("=" * 60)

    demo_dir = os.path.dirname(os.path.abspath(__file__))
    app_log, access_log = create_demo_logs(demo_dir)

    # 1. 分析应用日志
    print("\n>>> 分析应用日志 (app.log)")
    analyzer = LogAnalyzer()
    summary = analyzer.analyze_file(app_log, log_type="app")
    analyzer.print_report(summary)

    # 2. 分析访问日志
    print("\n\n>>> 分析访问日志 (access.log)")
    analyzer2 = LogAnalyzer()
    summary2 = analyzer2.analyze_file(access_log, log_type="access")
    analyzer2.print_report(summary2)

    # 3. 自动检测格式
    print("\n\n>>> 自动检测格式分析 (auto)")
    analyzer3 = LogAnalyzer()
    summary3 = analyzer3.analyze_file(app_log, log_type="auto")
    print(f"自动模式解析行数: {summary3['parsed_lines']}/{summary3['total_lines']}")

    # 清理
    cleanup_demo_logs(demo_dir)

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
