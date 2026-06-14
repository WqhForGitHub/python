"""
任务调度器（定时执行）
功能：
    - 支持一次性延时任务（after N seconds）
    - 支持周期性任务（interval）
    - 支持 cron 风格的简化触发：每分钟/每小时/每天某时刻
    - 任务并发执行（线程池）
    - 任务取消、列表查看、运行日志
    - 类似一个轻量的 schedule + threading.Timer 综合体
"""

import os
import time
import uuid
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor


class Task:
    def __init__(self, tid, func, args, kwargs, kind, **meta):
        self.id = tid
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.kind = kind          # 'once' / 'interval' / 'daily'
        self.meta = meta
        self.runs = 0
        self.last_run = None
        self.last_result = None
        self.last_error = None
        self.cancelled = False
        self.next_run = meta.get("next_run")

    def run(self):
        try:
            self.last_result = self.func(*self.args, **self.kwargs)
            self.last_error = None
        except Exception as e:
            self.last_error = str(e)
        finally:
            self.runs += 1
            self.last_run = datetime.now()


class Scheduler:
    """轻量任务调度器"""

    def __init__(self, max_workers: int = 4, tick: float = 0.2):
        self.tasks: dict[str, Task] = {}
        self.tick = tick                 # 调度器轮询间隔(s)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        self.log = []

    # -------- 添加任务 --------
    def after(self, delay: float, func, *args, **kwargs) -> str:
        tid = self._mkid()
        t = Task(tid, func, args, kwargs, "once",
                 next_run=datetime.now() + timedelta(seconds=delay))
        self._add(t)
        return tid

    def every(self, interval: float, func, *args, **kwargs) -> str:
        tid = self._mkid()
        t = Task(tid, func, args, kwargs, "interval",
                 interval=interval,
                 next_run=datetime.now() + timedelta(seconds=interval))
        self._add(t)
        return tid

    def daily_at(self, hh: int, mm: int, func, *args, **kwargs) -> str:
        """每日 hh:mm 执行（演示用，未涉及时区）"""
        tid = self._mkid()
        now = datetime.now()
        run_at = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if run_at <= now:
            run_at += timedelta(days=1)
        t = Task(tid, func, args, kwargs, "daily",
                 hh=hh, mm=mm, next_run=run_at)
        self._add(t)
        return tid

    def cancel(self, tid: str) -> bool:
        with self._lock:
            t = self.tasks.get(tid)
            if not t:
                return False
            t.cancelled = True
            return True

    def list(self) -> list:
        with self._lock:
            return [
                {
                    "id": t.id, "kind": t.kind, "runs": t.runs,
                    "next_run": t.next_run.strftime("%H:%M:%S") if t.next_run else "-",
                    "last_error": t.last_error,
                    "cancelled": t.cancelled,
                }
                for t in self.tasks.values()
            ]

    # -------- 启停 --------
    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        self.executor.shutdown(wait=False)

    # -------- 内部 --------
    def _mkid(self):
        return uuid.uuid4().hex[:8]

    def _add(self, t: Task):
        with self._lock:
            self.tasks[t.id] = t

    def _loop(self):
        while self._running:
            now = datetime.now()
            due = []
            with self._lock:
                for t in list(self.tasks.values()):
                    if t.cancelled:
                        continue
                    if t.next_run and now >= t.next_run:
                        due.append(t)
                        if t.kind == "once":
                            t.next_run = None
                            t.cancelled = True
                        elif t.kind == "interval":
                            t.next_run = now + timedelta(seconds=t.meta["interval"])
                        elif t.kind == "daily":
                            t.next_run = t.next_run + timedelta(days=1)

            for t in due:
                self.log.append(
                    f"[{now.strftime('%H:%M:%S')}] run task {t.id} ({t.kind})"
                )
                self.executor.submit(t.run)

            time.sleep(self.tick)


# ==================== Demo ====================

# 一些示例任务函数
_count = {"n": 0}


def heartbeat(label="❤"):
    _count["n"] += 1
    print(f"    [{datetime.now().strftime('%H:%M:%S')}] heartbeat {label} #{_count['n']}")


def hello(name="world"):
    print(f"    [{datetime.now().strftime('%H:%M:%S')}] hello, {name}!")


def fail_task():
    raise RuntimeError("boom!")


if __name__ == "__main__":
    print("=" * 60)
    print("  任务调度器 Demo")
    print("=" * 60)

    sch = Scheduler(max_workers=3, tick=0.1)
    sch.start()

    # 1. 添加各种任务
    print("\n--- 1. 注册任务 ---")
    tid_once  = sch.after(1.5, hello, "Alice")
    tid_int   = sch.every(0.7, heartbeat, "♥")
    tid_fail  = sch.every(1.0, fail_task)
    print(f"  one-shot   id={tid_once}, after 1.5s")
    print(f"  interval   id={tid_int}, every 0.7s")
    print(f"  failing    id={tid_fail}, every 1.0s")

    # 2. 运行 4 秒
    print("\n--- 2. 运行 4 秒 ---")
    time.sleep(4)

    # 3. 查看任务
    print("\n--- 3. 当前任务列表 ---")
    for info in sch.list():
        print(f"  {info}")

    # 4. 取消周期任务
    print("\n--- 4. 取消周期任务 ---")
    sch.cancel(tid_int)
    sch.cancel(tid_fail)
    print(f"  已取消 {tid_int}, {tid_fail}")

    # 5. 演示 daily_at（不实际等到第二天，只展示 next_run）
    print("\n--- 5. 注册 daily_at 任务 ---")
    tid_daily = sch.daily_at(8, 30, hello, "Bob")
    info = next(i for i in sch.list() if i["id"] == tid_daily)
    print(f"  daily_at 08:30 -> next_run={info['next_run']}")

    # 6. 调度器日志
    print("\n--- 6. 调度日志（前 8 条） ---")
    for line in sch.log[:8]:
        print(f"  {line}")

    sch.stop()

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
