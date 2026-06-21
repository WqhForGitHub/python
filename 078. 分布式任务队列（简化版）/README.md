# 78. 分布式任务队列（简化版）

纯 Python（仅使用标准库 `socket` / `threading` / `queue` / `json`）实现的简化版分布式任务队列，用于演示分布式系统中常见的「Producer / Broker / Worker」三角架构。

## 架构

```
┌──────────┐   submit/result    ┌──────────┐   fetch/report   ┌──────────┐
│ Producer │ ─────────────────► │  Broker  │ ◄─────────────── │  Worker  │
└──────────┘                    └──────────┘                  └──────────┘
                          (TCP socket + JSON 行协议)
```

- **Broker**：调度中心，维护待处理任务队列与结果表，负责派发任务、收集结果
- **Worker**：任务执行节点，可启动多个，轮询拉取任务并上报结果
- **Producer**：任务生产者，向 Broker 提交任务并查询结果

## 文件说明

| 文件 | 说明 |
|------|------|
| `broker.py`   | 任务调度中心，监听 9999 端口 |
| `worker.py`   | 任务执行节点，可启动多个 |
| `producer.py` | 任务生产者示例 |
| `client.py`   | 与 Broker 通信的客户端工具库 |
| `tasks.py`    | 任务函数注册表（add / multiply / slow_square / factorial / reverse_str） |

## 通信协议

基于 TCP，每条消息一行 JSON，以 `\n` 结尾。

| Action  | 发起方     | 请求参数                      | 响应 data            |
|---------|-----------|------------------------------|---------------------|
| submit  | Producer  | `{task: {func, args}}`       | `{task_id}`         |
| fetch   | Worker    | -                            | `task` 或 `null`    |
| report  | Worker    | `{task_id, result}`          | -                   |
| result  | Producer  | `{task_id}`                  | `{status, result}`  |
| stats   | Producer  | -                            | `{total, done, ...}`|

## 运行方式

打开 **3 个终端**（顺序执行）：

```bash
# 终端 1：启动 Broker
python broker.py

# 终端 2：启动 Worker（可在多个终端中启动多个 Worker 模拟分布式）
python worker.py worker-A
python worker.py worker-B   # 另一个终端

# 终端 3：启动 Producer 提交任务
python producer.py
```

可观察到任务被多个 Worker 并行抢占执行，最终 Producer 收到全部结果。

## 设计要点

1. **线程安全**：Broker 使用 `queue.Queue` + `threading.Lock` 保护共享状态
2. **解耦**：Producer / Worker 都只依赖 `BrokerClient`，不关心彼此
3. **可扩展任务**：在 [tasks.py](tasks.py) 的 `TASK_REGISTRY` 注册新函数即可
4. **简化版限制**：
   - 无持久化（Broker 重启后任务丢失）
   - 无任务重试 / 超时机制
   - 短连接请求-响应模式（每个请求一次新 TCP）
