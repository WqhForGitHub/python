"""
分布式任务队列 - Producer（任务生产者）

向 Broker 批量提交任务，并轮询查询任务结果。
"""

import time

from client import BrokerClient


def main():
    client = BrokerClient()

    # 1. 批量提交任务
    tasks = [
        ("add", [1, 2]),
        ("multiply", [3, 7]),
        ("slow_square", [5]),
        ("factorial", [6]),
        ("reverse_str", ["hello, distributed task queue"]),
        ("slow_square", [9]),
        ("add", [100, 200]),
    ]

    task_ids = []
    print("=" * 50)
    print("提交任务：")
    print("=" * 50)
    for func, args in tasks:
        tid = client.submit_task(func, args)
        task_ids.append((tid, func, args))
        print(f"  -> {func}{tuple(args)}  task_id={tid}")

    # 2. 轮询查询所有结果
    print("\n" + "=" * 50)
    print("等待任务执行完成：")
    print("=" * 50)
    pending = set(t[0] for t in task_ids)
    results = {}

    while pending:
        time.sleep(1)
        stats = client.get_stats()
        print(f"[stats] {stats}")

        for tid in list(pending):
            info = client.query_result(tid)
            if info["status"] == "done":
                results[tid] = info["result"]
                pending.remove(tid)

    # 3. 打印结果
    print("\n" + "=" * 50)
    print("最终结果：")
    print("=" * 50)
    for tid, func, args in task_ids:
        print(f"{func}{tuple(args)}  =>  {results[tid]}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"出错：{e}")
