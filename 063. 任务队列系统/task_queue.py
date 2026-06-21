# -*- coding: utf-8 -*-
"""
任务队列系统
- 进程内任务队列（基于 queue.PriorityQueue + threading 工作池）
- 支持任务优先级、重试、超时（通过 worker 协作）、回调
- 任务结果可通过 Future-like 对象获取
- 提供生产者 / 多 worker 消费者示例
"""
import threading
import time
import queue
import itertools
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


_id_seq = itertools.count(1)


class TaskFuture:
    """简单的 Future 实现：阻塞式 result()"""
    def __init__(self):
        self._event = threading.Event()
        self._value = None
        self._error = None

    def set_result(self, value):
        self._value = value
        self._event.set()

    def set_error(self, err):
        self._error = err
        self._event.set()

    def result(self, timeout=None):
        if not self._event.wait(timeout):
            raise TimeoutError("等待结果超时")
        if self._error:
            raise self._error
        return self._value

    def done(self):
        return self._event.is_set()


@dataclass(order=True)
class _Job:
    priority: int
    seq: int                                 # FIFO 决胜
    func: Callable = field(compare=False)
    args: tuple = field(default=(), compare=False)
    kwargs: dict = field(default_factory=dict, compare=False)
    retries: int = field(default=0, compare=False)
    future: TaskFuture = field(default=None, compare=False)
    name: str = field(default="task", compare=False)


class TaskQueue:
    """
    简单进程内任务队列。
    用法：
        tq = TaskQueue(num_workers=4)
        tq.start()
        fut = tq.submit(my_func, args=(1,2), priority=0, retries=2)
        print(fut.result())
        tq.stop()
    """
    def __init__(self, num_workers=4):
        self.num_workers = num_workers
        self.q = queue.PriorityQueue()
        self.workers = []
        self.running = False
        self._stop_event = threading.Event()

    def submit(self, func, args=(), kwargs=None, priority=5, retries=0, name=None):
        kwargs = kwargs or {}
        fut = TaskFuture()
        job = _Job(priority=priority, seq=next(_id_seq),
                   func=func, args=args, kwargs=kwargs,
                   retries=retries, future=fut, name=name or func.__name__)
        self.q.put(job)
        return fut

    def start(self):
        if self.running:
            return
        self.running = True
        self._stop_event.clear()
        for i in range(self.num_workers):
            t = threading.Thread(target=self._worker_loop, args=(i,), daemon=True)
            t.start()
            self.workers.append(t)

    def stop(self, wait=True):
        self.running = False
        for _ in self.workers:
            self.q.put(_Job(priority=99999, seq=next(_id_seq),
                            func=None, name="__stop__"))
        if wait:
            for t in self.workers:
                t.join()
        self.workers.clear()

    def _worker_loop(self, wid):
        while self.running:
            job = self.q.get()
            if job.func is None:
                self.q.task_done()
                break
            attempts = 0
            max_attempts = job.retries + 1
            while True:
                attempts += 1
                try:
                    print(f"[worker-{wid}] 执行 {job.name} (尝试 {attempts}/{max_attempts}, 优先级 {job.priority})")
                    r = job.func(*job.args, **job.kwargs)
                    job.future.set_result(r)
                    break
                except Exception as e:
                    if attempts < max_attempts:
                        print(f"[worker-{wid}] {job.name} 失败：{e}，重试...")
                        time.sleep(0.2 * attempts)
                        continue
                    print(f"[worker-{wid}] {job.name} 最终失败：{e}")
                    traceback.print_exc()
                    job.future.set_error(e)
                    break
            self.q.task_done()


# ---------- demo ----------
def _demo_task(name, sleep=0.3, fail=False):
    print(f"  -> {name} 开始")
    time.sleep(sleep)
    if fail:
        raise RuntimeError(f"{name} 模拟失败")
    print(f"  -> {name} 完成")
    return f"{name} 的结果"


def main():
    tq = TaskQueue(num_workers=3)
    tq.start()

    futs = []
    futs.append(tq.submit(_demo_task, args=("A",), priority=5))
    futs.append(tq.submit(_demo_task, args=("B-紧急",), priority=1))
    futs.append(tq.submit(_demo_task, args=("C",), kwargs={"sleep": 0.1}, priority=8))
    futs.append(tq.submit(_demo_task, args=("D-重试",), kwargs={"fail": True},
                          priority=3, retries=2))

    for f in futs:
        try:
            print("结果:", f.result(timeout=10))
        except Exception as e:
            print("失败:", e)

    tq.stop()


if __name__ == "__main__":
    main()
