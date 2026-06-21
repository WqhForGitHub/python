# 63. 任务队列系统

进程内任务队列，基于 `queue.PriorityQueue` + 线程工作池。

## 特性
- 任务优先级（数值小优先）
- 失败自动重试
- Future 风格的结果获取（result / timeout）
- 多 worker 并发消费

## 用法
```python
from task_queue import TaskQueue
tq = TaskQueue(num_workers=4)
tq.start()
fut = tq.submit(my_func, args=(1, 2), priority=1, retries=2)
print(fut.result())
tq.stop()
```

直接运行示例：
```
python task_queue.py
```
