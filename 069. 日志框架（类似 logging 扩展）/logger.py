# -*- coding: utf-8 -*-
"""
日志框架（类似 logging 扩展）
- 纯 Python 实现，不依赖标准库 logging
- 特性：
  * 等级：DEBUG < INFO < WARNING < ERROR < CRITICAL
  * Handler：StreamHandler / FileHandler / RotatingFileHandler
  * Formatter：自定义格式串（%(time)s %(level)s %(name)s %(message)s）
  * Filter：函数式过滤
  * 层级 Logger（"app", "app.db" 自动继承父级 handlers/level）
  * 上下文（extra）字段注入
  * 彩色控制台输出（可关闭）

用法：
    python logger.py
"""
import os
import sys
import time
import threading
from datetime import datetime
from pathlib import Path


# ---------- 等级 ----------
DEBUG, INFO, WARNING, ERROR, CRITICAL = 10, 20, 30, 40, 50
LEVEL_NAMES = {DEBUG: "DEBUG", INFO: "INFO", WARNING: "WARNING",
               ERROR: "ERROR", CRITICAL: "CRITICAL"}
NAME_LEVELS = {v: k for k, v in LEVEL_NAMES.items()}

_COLORS = {
    DEBUG: "\033[36m",      # cyan
    INFO: "\033[32m",       # green
    WARNING: "\033[33m",    # yellow
    ERROR: "\033[31m",      # red
    CRITICAL: "\033[35;1m", # bold magenta
}
_RESET = "\033[0m"


# ---------- 记录 ----------
class LogRecord:
    def __init__(self, name, level, message, extra=None):
        self.name = name
        self.level = level
        self.levelname = LEVEL_NAMES[level]
        self.message = message
        self.time = datetime.now()
        self.thread = threading.current_thread().name
        self.extra = extra or {}


# ---------- 格式化 ----------
class Formatter:
    def __init__(self, fmt="%(time)s [%(level)s] %(name)s: %(message)s",
                 datefmt="%Y-%m-%d %H:%M:%S"):
        self.fmt = fmt
        self.datefmt = datefmt

    def format(self, record: LogRecord):
        d = {
            "time": record.time.strftime(self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.message,
            "thread": record.thread,
        }
        d.update(record.extra)
        try:
            return self.fmt % d
        except KeyError as e:
            return f"[FormatError missing {e}] {record.message}"


# ---------- Handlers ----------
class Handler:
    def __init__(self, level=DEBUG, formatter=None):
        self.level = level
        self.formatter = formatter or Formatter()
        self.filters = []
        self._lock = threading.Lock()

    def add_filter(self, fn):
        self.filters.append(fn)

    def handle(self, record):
        if record.level < self.level:
            return
        for f in self.filters:
            if not f(record):
                return
        text = self.formatter.format(record)
        with self._lock:
            self.emit(record, text)

    def emit(self, record, text):
        raise NotImplementedError


class StreamHandler(Handler):
    def __init__(self, stream=None, color=True, **kw):
        super().__init__(**kw)
        self.stream = stream or sys.stdout
        self.color = color and self._supports_color()

    @staticmethod
    def _supports_color():
        if os.environ.get("NO_COLOR"):
            return False
        if os.name == "nt":
            return os.environ.get("TERM") not in (None, "dumb") or "WT_SESSION" in os.environ
        return sys.stdout.isatty()

    def emit(self, record, text):
        if self.color:
            text = _COLORS.get(record.level, "") + text + _RESET
        self.stream.write(text + "\n")
        self.stream.flush()


class FileHandler(Handler):
    def __init__(self, path, encoding="utf-8", **kw):
        super().__init__(**kw)
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.encoding = encoding
        self._fp = open(self.path, "a", encoding=self.encoding)

    def emit(self, record, text):
        self._fp.write(text + "\n")
        self._fp.flush()

    def close(self):
        try: self._fp.close()
        except Exception: pass


class RotatingFileHandler(FileHandler):
    """按大小轮转：超过 max_bytes 后重命名为 .1, .2, ..."""
    def __init__(self, path, max_bytes=1024 * 1024, backup_count=3, **kw):
        super().__init__(path, **kw)
        self.max_bytes = max_bytes
        self.backup_count = backup_count

    def emit(self, record, text):
        self._rollover_if_needed(len(text) + 1)
        super().emit(record, text)

    def _rollover_if_needed(self, incoming):
        try:
            size = self.path.stat().st_size
        except FileNotFoundError:
            return
        if size + incoming <= self.max_bytes:
            return
        self._fp.close()
        # 轮转
        for i in range(self.backup_count - 1, 0, -1):
            src = self.path.with_suffix(self.path.suffix + f".{i}")
            dst = self.path.with_suffix(self.path.suffix + f".{i + 1}")
            if src.exists(): src.replace(dst)
        first = self.path.with_suffix(self.path.suffix + ".1")
        self.path.replace(first)
        self._fp = open(self.path, "a", encoding=self.encoding)


# ---------- Logger ----------
class Logger:
    _registry = {}
    _lock = threading.RLock()

    def __init__(self, name, parent=None):
        self.name = name
        self.level = INFO if parent is None else None  # None 表示继承
        self.parent = parent
        self.handlers = []
        self.propagate = True

    # ---- 等级判定 ----
    @property
    def effective_level(self):
        node = self
        while node is not None:
            if node.level is not None:
                return node.level
            node = node.parent
        return INFO

    def set_level(self, level):
        if isinstance(level, str):
            level = NAME_LEVELS[level.upper()]
        self.level = level

    def add_handler(self, h: Handler):
        self.handlers.append(h)

    def remove_handlers(self):
        for h in self.handlers:
            if isinstance(h, FileHandler):
                h.close()
        self.handlers.clear()

    # ---- 日志方法 ----
    def log(self, level, msg, *args, extra=None):
        if level < self.effective_level:
            return
        if args:
            try: msg = msg % args
            except Exception: msg = f"{msg} {args}"
        record = LogRecord(self.name, level, msg, extra)
        node = self
        while node is not None:
            for h in node.handlers:
                h.handle(record)
            if not node.propagate:
                break
            node = node.parent

    def debug(self, msg, *args, **kw):    self.log(DEBUG, msg, *args, **kw)
    def info(self, msg, *args, **kw):     self.log(INFO, msg, *args, **kw)
    def warning(self, msg, *args, **kw):  self.log(WARNING, msg, *args, **kw)
    def error(self, msg, *args, **kw):    self.log(ERROR, msg, *args, **kw)
    def critical(self, msg, *args, **kw): self.log(CRITICAL, msg, *args, **kw)


def get_logger(name="root"):
    with Logger._lock:
        if name in Logger._registry:
            return Logger._registry[name]
        # 找父
        if "." in name:
            parent_name = name.rsplit(".", 1)[0]
            parent = get_logger(parent_name)
        elif name == "root":
            parent = None
        else:
            parent = get_logger("root")
        logger = Logger(name, parent)
        Logger._registry[name] = logger
        return logger


# 默认根 logger
_root = get_logger("root")
_root.add_handler(StreamHandler())


# ---------- demo ----------
def demo():
    log = get_logger("app")
    log.set_level("DEBUG")
    log.add_handler(FileHandler("logs/app.log",
                                formatter=Formatter("%(time)s [%(level)s] %(message)s")))
    log.add_handler(RotatingFileHandler("logs/app_rot.log", max_bytes=2048,
                                        backup_count=2))

    log.debug("调试信息 %s", "x")
    log.info("正常信息")
    log.warning("警告: 磁盘剩余 %d%%", 9)
    log.error("出错了: %s", "数据库连接失败")
    log.critical("致命错误！")

    db = get_logger("app.db")
    db.info("子 logger 自动继承等级和 handlers")

    # 过滤器：屏蔽包含 secret 的消息
    def no_secret(record):
        return "secret" not in record.message

    log.handlers[0].add_filter(no_secret)
    log.info("This is a secret message")  # 仅控制台不显示？这里是子 handler 上的 filter
    log.info("普通信息再来一条")

    # 上下文
    log.info("用户操作", extra={"user": "alice"})

    # 写入轮转测试
    for i in range(80):
        db.info("rotating %d - %s", i, "x" * 30)


if __name__ == "__main__":
    demo()
