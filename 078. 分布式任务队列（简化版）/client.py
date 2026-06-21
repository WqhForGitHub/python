"""
分布式任务队列 - 客户端工具库

封装与 Broker 通信的细节：
    - submit_task(func, args)  提交任务，返回 task_id
    - fetch_task()             拉取一个待执行任务
    - report_result(...)       上报任务结果
    - query_result(task_id)    查询任务结果
    - get_stats()              获取队列统计
"""

import socket
import json


class BrokerClient:
    def __init__(self, host="127.0.0.1", port=9999, timeout=5.0):
        self.host = host
        self.port = port
        self.timeout = timeout

    # ---------------- 对外接口 ----------------
    def submit_task(self, func: str, args: list) -> str:
        """提交一个任务，返回 task_id"""
        resp = self._request({
            "action": "submit",
            "task": {"func": func, "args": args},
        })
        if not resp.get("ok"):
            raise RuntimeError(resp.get("error", "submit 失败"))
        return resp["data"]["task_id"]

    def fetch_task(self):
        """拉取一个任务，无任务时返回 None"""
        resp = self._request({"action": "fetch"})
        if not resp.get("ok"):
            raise RuntimeError(resp.get("error", "fetch 失败"))
        return resp["data"]  # 可能为 None

    def report_result(self, task_id: str, result):
        """上报任务结果"""
        resp = self._request({
            "action": "report",
            "task_id": task_id,
            "result": result,
        })
        if not resp.get("ok"):
            raise RuntimeError(resp.get("error", "report 失败"))

    def query_result(self, task_id: str) -> dict:
        """查询任务结果，返回 {status, result}"""
        resp = self._request({"action": "result", "task_id": task_id})
        if not resp.get("ok"):
            raise RuntimeError(resp.get("error", "查询失败"))
        return resp["data"]

    def get_stats(self) -> dict:
        resp = self._request({"action": "stats"})
        if not resp.get("ok"):
            raise RuntimeError(resp.get("error", "stats 失败"))
        return resp["data"]

    # ---------------- 内部网络 ----------------
    def _request(self, msg: dict) -> dict:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        try:
            sock.connect((self.host, self.port))
            payload = (json.dumps(msg, ensure_ascii=False) + "\n").encode("utf-8")
            sock.sendall(payload)

            # 读响应（一行）
            buf = b""
            while True:
                ch = sock.recv(1)
                if not ch:
                    break
                if ch == b"\n":
                    break
                buf += ch
            return json.loads(buf.decode("utf-8")) if buf else {}
        finally:
            sock.close()
