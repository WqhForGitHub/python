"""
分布式任务队列 - Broker（任务调度中心）

职责：
    1. 接收 Producer 提交的任务，放入待处理队列
    2. 向 Worker 分发任务
    3. 接收 Worker 上报的执行结果，存入结果表
    4. 支持 Producer 查询结果

通信协议：基于 TCP socket，使用 JSON 行协议（每行一条 JSON 消息）

消息格式：
    Producer -> Broker:
        {"action": "submit",  "task": {...}}                  提交任务
        {"action": "result",  "task_id": "..."}               查询结果
    Worker -> Broker:
        {"action": "fetch"}                                   拉取任务
        {"action": "report",  "task_id": "...", "result": ..} 上报结果
    Broker 响应：
        {"ok": true/false, "data": ...}
"""

import socket
import threading
import json
import uuid
import queue
import time


class Broker:
    def __init__(self, host="127.0.0.1", port=9999):
        self.host = host
        self.port = port

        # 待处理任务队列（线程安全）
        self.task_queue = queue.Queue()
        # 任务结果表 {task_id: {"status": "...", "result": ...}}
        self.results = {}
        # 任务总表 {task_id: task_dict}（便于追踪）
        self.tasks = {}

        self.lock = threading.Lock()
        self.running = False

    # ---------------- 公共方法 ----------------
    def start(self):
        """启动 Broker，监听客户端连接"""
        self.running = True
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.listen(50)
        print(f"[Broker] 启动成功，监听 {self.host}:{self.port}")

        try:
            while self.running:
                client, addr = sock.accept()
                t = threading.Thread(
                    target=self._handle_client, args=(client, addr), daemon=True
                )
                t.start()
        except KeyboardInterrupt:
            print("\n[Broker] 收到中断信号，正在关闭...")
        finally:
            sock.close()

    # ---------------- 内部处理 ----------------
    def _handle_client(self, client: socket.socket, addr):
        """处理一个客户端的请求（一次性请求-响应）"""
        try:
            # 读完整一行
            data = self._recv_line(client)
            if not data:
                return
            msg = json.loads(data)
            response = self._dispatch(msg)
            self._send_line(client, response)
        except Exception as e:
            err = {"ok": False, "error": str(e)}
            try:
                self._send_line(client, err)
            except Exception:
                pass
            print(f"[Broker] 客户端 {addr} 处理异常: {e}")
        finally:
            client.close()

    def _dispatch(self, msg: dict) -> dict:
        """根据 action 字段分发处理"""
        action = msg.get("action")

        if action == "submit":
            return self._on_submit(msg.get("task", {}))
        elif action == "fetch":
            return self._on_fetch()
        elif action == "report":
            return self._on_report(msg.get("task_id"), msg.get("result"))
        elif action == "result":
            return self._on_query_result(msg.get("task_id"))
        elif action == "stats":
            return self._on_stats()
        else:
            return {"ok": False, "error": f"未知 action: {action}"}

    # ---- 各 action 处理 ----
    def _on_submit(self, task: dict) -> dict:
        task_id = str(uuid.uuid4())
        task["task_id"] = task_id
        task["submit_time"] = time.time()

        with self.lock:
            self.tasks[task_id] = task
            self.results[task_id] = {"status": "pending", "result": None}
        self.task_queue.put(task)

        print(f"[Broker] 收到任务 {task_id}: {task.get('func')}({task.get('args')})")
        return {"ok": True, "data": {"task_id": task_id}}

    def _on_fetch(self) -> dict:
        try:
            task = self.task_queue.get_nowait()
            with self.lock:
                self.results[task["task_id"]]["status"] = "running"
            print(f"[Broker] 派发任务 {task['task_id']} 给 Worker")
            return {"ok": True, "data": task}
        except queue.Empty:
            return {"ok": True, "data": None}

    def _on_report(self, task_id: str, result) -> dict:
        if not task_id:
            return {"ok": False, "error": "task_id 为空"}
        with self.lock:
            if task_id not in self.results:
                return {"ok": False, "error": "未知 task_id"}
            self.results[task_id]["status"] = "done"
            self.results[task_id]["result"] = result
        print(f"[Broker] 任务 {task_id} 完成 -> {result}")
        return {"ok": True}

    def _on_query_result(self, task_id: str) -> dict:
        if not task_id:
            return {"ok": False, "error": "task_id 为空"}
        with self.lock:
            info = self.results.get(task_id)
        if info is None:
            return {"ok": False, "error": "未知 task_id"}
        return {"ok": True, "data": info}

    def _on_stats(self) -> dict:
        with self.lock:
            total = len(self.tasks)
            done = sum(1 for v in self.results.values() if v["status"] == "done")
            running = sum(1 for v in self.results.values() if v["status"] == "running")
            pending = sum(1 for v in self.results.values() if v["status"] == "pending")
        return {
            "ok": True,
            "data": {
                "total": total,
                "done": done,
                "running": running,
                "pending": pending,
            },
        }

    # ---------------- 网络工具 ----------------
    @staticmethod
    def _recv_line(sock: socket.socket) -> str:
        """读取一行（以 \\n 结尾）数据"""
        buf = b""
        while True:
            ch = sock.recv(1)
            if not ch:
                break
            if ch == b"\n":
                break
            buf += ch
        return buf.decode("utf-8")

    @staticmethod
    def _send_line(sock: socket.socket, msg: dict):
        data = (json.dumps(msg, ensure_ascii=False) + "\n").encode("utf-8")
        sock.sendall(data)


if __name__ == "__main__":
    Broker().start()
