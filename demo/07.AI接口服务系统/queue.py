"""异步任务队列。

使用 asyncio.Queue + 后台 worker 协程实现：
- 提交任务后立即返回 task_id
- worker 协程从队列取任务，调用 LLM，更新数据库
- 失败自动重试（最多 TASK_MAX_RETRIES 次）

应用启动时通过 lifespan 启动 worker，关闭时取消。
"""
import asyncio
import threading
from datetime import datetime

import config
import crud.task
import llm
from database import SessionLocal


class TaskQueue:
    def __init__(self, workers: int) -> None:
        self.workers = workers
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._tasks: list[asyncio.Task] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    async def start(self) -> None:
        self._loop = asyncio.get_running_loop()
        for i in range(self.workers):
            t = asyncio.create_task(self._worker(i), name=f"llm-worker-{i}")
            self._tasks.append(t)

    async def stop(self) -> None:
        for t in self._tasks:
            t.cancel()
        for t in self._tasks:
            try:
                await t
            except asyncio.CancelledError:
                pass
        self._tasks.clear()

    def enqueue(self, task_id: str) -> None:
        """提交任务到队列。需在事件循环中调用。"""
        assert self._loop is not None
        self._loop.call_soon_threadsafe(self._queue.put_nowait, task_id)

    async def _worker(self, idx: int) -> None:
        while True:
            task_id = await self._queue.get()
            try:
                await self._process(task_id)
            except Exception as e:  # noqa: BLE001
                print(f"[worker-{idx}] 任务 {task_id} 处理异常：{e}")
            finally:
                self._queue.task_done()

    async def _process(self, task_id: str) -> None:
        db = SessionLocal()
        try:
            task = crud.task.get_task_by_id(db, task_id)
            if task is None:
                return
            crud.task.mark_running(db, task)

            messages = [{"role": "user", "content": task.prompt}]
            try:
                reply, model, provider = await llm.chat(messages, model=task.model)
                crud.task.mark_succeeded(db, task, reply, model)
            except Exception as e:  # noqa: BLE001
                # 重试逻辑
                task.retries += 1
                if task.retries <= config.TASK_MAX_RETRIES:
                    crud.task.mark_retrying(db, task, str(e))
                    # 重新入队
                    self._queue.put_nowait(task_id)
                else:
                    crud.task.mark_failed(db, task, str(e))
        finally:
            db.close()


# 全局单例（在 lifespan 中 start/stop）
task_queue = TaskQueue(config.TASK_QUEUE_WORKERS)
