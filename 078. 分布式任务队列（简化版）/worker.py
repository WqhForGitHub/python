"""
分布式任务队列 - Worker（任务执行节点）

职责：
    1. 周期性向 Broker 拉取任务
    2. 执行任务（通过 tasks.TASK_REGISTRY 查找函数）
    3. 把结果上报给 Broker

可启动多个 Worker 进程模拟分布式执行。

用法：
    python worker.py              # 启动一个 worker
    python worker.py worker-A     # 指定 worker 名称
"""

import sys
import time
import traceback

from client import BrokerClient
from tasks import execute


class Worker:
    def __init__(self, name: str = "worker", host="127.0.0.1", port=9999,
                 poll_interval: float = 1.0):
        self.name = name
        self.client = BrokerClient(host, port)
        self.poll_interval = poll_interval
        self.running = False

    def start(self):
        self.running = True
        print(f"[{self.name}] 已启动，等待任务...")
        while self.running:
            try:
                task = self.client.fetch_task()
            except Exception as e:
                print(f"[{self.name}] 拉取任务失败: {e}")
                time.sleep(self.poll_interval)
                continue

            if task is None:
                # 没有任务，稍后再来
                time.sleep(self.poll_interval)
                continue

            self._run_task(task)

    def _run_task(self, task: dict):
        task_id = task.get("task_id")
        func = task.get("func")
        args = task.get("args", [])
        print(f"[{self.name}] 开始执行 {task_id}: {func}({args})")

        try:
            result = execute(func, args)
            payload = {"ok": True, "value": result}
        except Exception as e:
            traceback.print_exc()
            payload = {"ok": False, "error": str(e)}

        try:
            self.client.report_result(task_id, payload)
            print(f"[{self.name}] 已上报 {task_id} -> {payload}")
        except Exception as e:
            print(f"[{self.name}] 上报失败: {e}")


if __name__ == "__main__":
    worker_name = sys.argv[1] if len(sys.argv) > 1 else "worker"
    try:
        Worker(worker_name).start()
    except KeyboardInterrupt:
        print(f"\n[{worker_name}] 已停止")
