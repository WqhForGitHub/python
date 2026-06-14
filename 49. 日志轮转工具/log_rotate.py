"""
日志轮转工具
功能：
    - 自实现的 RotatingFileHandler：
        * 按文件大小轮转（size-based）
        * 按时间轮转（time-based: hour/day/midnight）
        * 保留 N 个备份，多余的自动删除
        * 可选 gzip 压缩备份
    - Logger 提供 debug/info/warn/error 方法
    - 兼容多线程：写入加锁
    - 不依赖 logging 标准库（手写一份小 logger 演示原理）
"""

import os
import gzip
import time
import shutil
import threading
from datetime import datetime, timedelta


LEVELS = {"DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40}


# ==================================================================
# 文件处理器
# ==================================================================

class SizeRotatingHandler:
    """按文件大小轮转：file -> file.1 -> file.2 ... 最多 backup_count 个"""

    def __init__(self, path: str, max_bytes: int = 1024,
                 backup_count: int = 3, compress: bool = False):
        self.path = path
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.compress = compress
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)

    def write(self, line: str):
        line = line.rstrip("\n") + "\n"
        with self._lock:
            self._rotate_if_needed(len(line.encode("utf-8")))
            with open(self.path, "ab") as f:
                f.write(line.encode("utf-8"))

    def _rotate_if_needed(self, incoming: int):
        if not os.path.isfile(self.path):
            return
        if os.path.getsize(self.path) + incoming <= self.max_bytes:
            return
        # 删除最老的
        ext = ".gz" if self.compress else ""
        oldest = f"{self.path}.{self.backup_count}{ext}"
        if os.path.isfile(oldest):
            os.remove(oldest)
        # 依次后移
        for i in range(self.backup_count - 1, 0, -1):
            src = f"{self.path}.{i}{ext}"
            dst = f"{self.path}.{i+1}{ext}"
            if os.path.isfile(src):
                os.rename(src, dst)
        # 当前 -> .1（压缩或不压缩）
        if self.compress:
            with open(self.path, "rb") as fin, \
                 gzip.open(f"{self.path}.1.gz", "wb") as fout:
                shutil.copyfileobj(fin, fout)
            os.remove(self.path)
        else:
            os.rename(self.path, f"{self.path}.1")


class TimeRotatingHandler:
    """按时间轮转：每小时 / 每天 / 每天 0 点"""

    def __init__(self, path: str, when: str = "day",
                 backup_count: int = 3, compress: bool = False):
        if when not in ("hour", "day", "midnight"):
            raise ValueError("when 必须是 hour/day/midnight")
        self.path = path
        self.when = when
        self.backup_count = backup_count
        self.compress = compress
        self._lock = threading.Lock()
        self._next_rollover = self._compute_next(datetime.now())
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)

    def _compute_next(self, now: datetime) -> datetime:
        if self.when == "hour":
            return (now.replace(minute=0, second=0, microsecond=0)
                    + timedelta(hours=1))
        if self.when in ("day", "midnight"):
            return (now.replace(hour=0, minute=0, second=0, microsecond=0)
                    + timedelta(days=1))
        return now + timedelta(days=1)

    def force_rollover(self):
        """显式触发一次轮转（演示用）"""
        with self._lock:
            self._do_rollover(datetime.now())

    def write(self, line: str):
        with self._lock:
            now = datetime.now()
            if now >= self._next_rollover and os.path.isfile(self.path):
                self._do_rollover(now)
                self._next_rollover = self._compute_next(now)
            with open(self.path, "ab") as f:
                f.write((line.rstrip("\n") + "\n").encode("utf-8"))

    def _do_rollover(self, now: datetime):
        if not os.path.isfile(self.path):
            return
        # 时间戳后缀
        if self.when == "hour":
            suffix = now.strftime("%Y%m%d-%H")
        else:
            suffix = now.strftime("%Y%m%d")
        ext = ".gz" if self.compress else ""
        target = f"{self.path}.{suffix}{ext}"
        # 防重名
        i = 1
        original = target
        while os.path.exists(target):
            target = f"{original}.{i}"
            i += 1

        if self.compress:
            with open(self.path, "rb") as fin, gzip.open(target, "wb") as fout:
                shutil.copyfileobj(fin, fout)
            os.remove(self.path)
        else:
            os.rename(self.path, target)

        # 清理过期备份
        self._purge_old()

    def _purge_old(self):
        d = os.path.dirname(os.path.abspath(self.path)) or "."
        prefix = os.path.basename(self.path) + "."
        files = sorted(
            (f for f in os.listdir(d) if f.startswith(prefix)),
            key=lambda x: os.path.getmtime(os.path.join(d, x)),
        )
        # 保留最新 backup_count 个
        excess = len(files) - self.backup_count
        for f in files[: max(0, excess)]:
            try:
                os.remove(os.path.join(d, f))
            except OSError:
                pass


# ==================================================================
# Logger
# ==================================================================

class Logger:
    def __init__(self, handler, level: str = "DEBUG"):
        self.handler = handler
        self.level = LEVELS.get(level, 10)

    def _log(self, lvl: str, msg: str):
        if LEVELS[lvl] < self.level:
            return
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.handler.write(f"{ts} [{lvl:<5}] {msg}")

    def debug(self, msg): self._log("DEBUG", msg)
    def info(self, msg): self._log("INFO", msg)
    def warn(self, msg): self._log("WARN", msg)
    def error(self, msg): self._log("ERROR", msg)


# ==================== Demo ====================

def list_log_files(folder: str, prefix: str):
    return sorted(f for f in os.listdir(folder) if f.startswith(prefix))


if __name__ == "__main__":
    print("=" * 60)
    print("  日志轮转工具 Demo")
    print("=" * 60)

    base = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(base, "logs")
    if os.path.exists(log_dir):
        shutil.rmtree(log_dir)
    os.makedirs(log_dir)

    # ==================================================================
    # 1. 按大小轮转
    # ==================================================================
    print("\n--- 1. 按大小轮转 (max_bytes=300, backup=3) ---")
    log_path = os.path.join(log_dir, "size.log")
    handler = SizeRotatingHandler(log_path, max_bytes=300, backup_count=3)
    logger = Logger(handler, level="DEBUG")

    for i in range(40):
        logger.info(f"size-rotate test message #{i:03d}: hello world")

    files = list_log_files(log_dir, "size.log")
    for f in files:
        full = os.path.join(log_dir, f)
        print(f"  {f:<20}  {os.path.getsize(full)} bytes")

    # ==================================================================
    # 2. 按大小轮转 + gzip 压缩备份
    # ==================================================================
    print("\n--- 2. 按大小轮转 + gzip 压缩 ---")
    gz_path = os.path.join(log_dir, "compressed.log")
    handler2 = SizeRotatingHandler(gz_path, max_bytes=300,
                                    backup_count=3, compress=True)
    log2 = Logger(handler2)
    for i in range(40):
        log2.warn(f"compressed-msg #{i}: data data data")

    files = list_log_files(log_dir, "compressed.log")
    for f in files:
        full = os.path.join(log_dir, f)
        print(f"  {f:<28}  {os.path.getsize(full)} bytes")

    # ==================================================================
    # 3. 按时间轮转（演示用 force_rollover）
    # ==================================================================
    print("\n--- 3. 按时间轮转（force_rollover 演示） ---")
    t_path = os.path.join(log_dir, "time.log")
    handler3 = TimeRotatingHandler(t_path, when="day", backup_count=3)
    log3 = Logger(handler3)

    for round_no in range(3):
        for i in range(5):
            log3.info(f"day#{round_no} msg#{i}")
        # 模拟时间到了：强制轮转
        handler3.force_rollover()
        time.sleep(0.01)
    log3.info("final entry")

    files = list_log_files(log_dir, "time.log")
    for f in files:
        full = os.path.join(log_dir, f)
        print(f"  {f:<35}  {os.path.getsize(full)} bytes")

    # ==================================================================
    # 4. 显示 size.log 内容片段
    # ==================================================================
    print("\n--- 4. 当前 size.log 内容（最后 5 行）---")
    with open(os.path.join(log_dir, "size.log"), "r", encoding="utf-8") as f:
        lines = f.readlines()
    for ln in lines[-5:]:
        print(f"  {ln.rstrip()}")

    # 清理
    shutil.rmtree(log_dir, ignore_errors=True)

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
