# -*- coding: utf-8 -*-
"""
Key-Value 存储系统
- 持久化的 KV 数据库（基于 AOF 追加日志 + 内存 dict）
- 类 Redis 操作：SET / GET / DEL / EXISTS / KEYS / EXPIRE / TTL / TYPE / SAVE
- 支持 TTL（过期时间）
- 支持 list / hash 简单数据结构（LPUSH/RPUSH/LRANGE, HSET/HGET/HGETALL）
- 内置网络服务器（基于 TCP 文本协议），可远程使用
- CLI 客户端

文件结构：
    kv.aof    追加日志，重启自动重放
    kv.snap   可选快照（SAVE 命令生成）
"""
import argparse
import json
import os
import socket
import sys
import threading
import time


class KVStore:
    def __init__(self, aof_path="kv.aof", snap_path="kv.snap"):
        self.aof_path = aof_path
        self.snap_path = snap_path
        self.lock = threading.RLock()
        self.data = {}     # key -> value
        self.types = {}    # key -> "str" | "list" | "hash"
        self.expires = {}  # key -> expire timestamp
        self._load()

    # ---------- 持久化 ----------
    def _load(self):
        if os.path.exists(self.snap_path):
            try:
                with open(self.snap_path, "r", encoding="utf-8") as f:
                    snap = json.load(f)
                self.data = snap.get("data", {})
                self.types = snap.get("types", {})
                self.expires = snap.get("expires", {})
                print(f"[*] 从快照恢复 {len(self.data)} 个键")
            except Exception as e:
                print(f"[!] 快照读取失败: {e}")

        if os.path.exists(self.aof_path):
            count = 0
            with open(self.aof_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        cmd = json.loads(line)
                        self._apply(cmd, persist=False)
                        count += 1
                    except Exception as e:
                        print(f"[!] AOF 行解析失败: {e}")
            print(f"[*] 重放 AOF {count} 条命令")

        self._aof_fp = open(self.aof_path, "a", encoding="utf-8")

    def _persist(self, cmd):
        self._aof_fp.write(json.dumps(cmd, ensure_ascii=False) + "\n")
        self._aof_fp.flush()

    def save_snapshot(self):
        with self.lock:
            self._cleanup_expired()
            snap = {"data": self.data, "types": self.types, "expires": self.expires}
            tmp = self.snap_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(snap, f, ensure_ascii=False)
            os.replace(tmp, self.snap_path)
            # 清空 AOF
            self._aof_fp.close()
            open(self.aof_path, "w", encoding="utf-8").close()
            self._aof_fp = open(self.aof_path, "a", encoding="utf-8")
            return f"OK saved {len(self.data)} keys"

    # ---------- 过期 ----------
    def _check_expire(self, key):
        exp = self.expires.get(key)
        if exp is not None and exp < time.time():
            self._delete_key(key)
            return True
        return False

    def _cleanup_expired(self):
        now = time.time()
        dead = [k for k, t in self.expires.items() if t < now]
        for k in dead:
            self._delete_key(k)

    def _delete_key(self, key):
        self.data.pop(key, None)
        self.types.pop(key, None)
        self.expires.pop(key, None)

    # ---------- 命令应用（重放或执行） ----------
    def _apply(self, cmd, persist=True):
        op = cmd[0].upper()
        if op == "SET":
            _, k, v = cmd
            self.data[k] = v
            self.types[k] = "str"
            self.expires.pop(k, None)
        elif op == "DEL":
            _, k = cmd
            self._delete_key(k)
        elif op == "EXPIRE":
            _, k, secs = cmd
            if k in self.data:
                self.expires[k] = time.time() + float(secs)
        elif op == "PERSIST":
            _, k = cmd
            self.expires.pop(k, None)
        elif op == "LPUSH":
            _, k, *items = cmd
            if k not in self.data:
                self.data[k] = []
                self.types[k] = "list"
            for it in items:
                self.data[k].insert(0, it)
        elif op == "RPUSH":
            _, k, *items = cmd
            if k not in self.data:
                self.data[k] = []
                self.types[k] = "list"
            self.data[k].extend(items)
        elif op == "HSET":
            _, k, f, v = cmd
            if k not in self.data:
                self.data[k] = {}
                self.types[k] = "hash"
            self.data[k][f] = v
        elif op == "HDEL":
            _, k, f = cmd
            if k in self.data and isinstance(self.data[k], dict):
                self.data[k].pop(f, None)
        if persist:
            self._persist(cmd)

    # ---------- 公开命令 ----------
    def execute(self, args):
        if not args:
            return "ERR empty command"
        op = args[0].upper()
        with self.lock:
            try:
                if op == "PING":
                    return "PONG"
                if op == "SET":
                    if len(args) < 3:
                        return "ERR usage: SET key value"
                    self._apply(["SET", args[1], args[2]])
                    return "OK"
                if op == "GET":
                    if len(args) != 2:
                        return "ERR usage: GET key"
                    k = args[1]
                    if self._check_expire(k):
                        return "(nil)"
                    if k not in self.data:
                        return "(nil)"
                    if self.types.get(k) != "str":
                        return f"ERR type {self.types.get(k)}"
                    return self.data[k]
                if op == "DEL":
                    if len(args) != 2:
                        return "ERR usage: DEL key"
                    existed = args[1] in self.data
                    self._apply(["DEL", args[1]])
                    return "1" if existed else "0"
                if op == "EXISTS":
                    k = args[1]
                    self._check_expire(k)
                    return "1" if k in self.data else "0"
                if op == "KEYS":
                    self._cleanup_expired()
                    return ", ".join(self.data.keys()) or "(empty)"
                if op == "TYPE":
                    return self.types.get(args[1], "none")
                if op == "EXPIRE":
                    if len(args) != 3:
                        return "ERR usage: EXPIRE key seconds"
                    if args[1] not in self.data:
                        return "0"
                    self._apply(["EXPIRE", args[1], float(args[2])])
                    return "1"
                if op == "TTL":
                    k = args[1]
                    if k not in self.data:
                        return "-2"
                    if k not in self.expires:
                        return "-1"
                    return f"{int(self.expires[k] - time.time())}"
                if op == "PERSIST":
                    self._apply(["PERSIST", args[1]])
                    return "OK"
                if op == "LPUSH":
                    self._apply(["LPUSH", args[1]] + list(args[2:]))
                    return str(len(self.data[args[1]]))
                if op == "RPUSH":
                    self._apply(["RPUSH", args[1]] + list(args[2:]))
                    return str(len(self.data[args[1]]))
                if op == "LRANGE":
                    if len(args) != 4:
                        return "ERR usage: LRANGE key start stop"
                    k = args[1]
                    if k not in self.data or self.types.get(k) != "list":
                        return "(empty)"
                    start, stop = int(args[2]), int(args[3])
                    items = self.data[k][start: stop + 1 if stop >= 0 else None]
                    return ", ".join(items) or "(empty)"
                if op == "HSET":
                    if len(args) != 4:
                        return "ERR usage: HSET key field value"
                    self._apply(["HSET", args[1], args[2], args[3]])
                    return "OK"
                if op == "HGET":
                    k, f = args[1], args[2]
                    if k not in self.data or self.types.get(k) != "hash":
                        return "(nil)"
                    return self.data[k].get(f, "(nil)")
                if op == "HGETALL":
                    k = args[1]
                    if k not in self.data or self.types.get(k) != "hash":
                        return "(empty)"
                    return ", ".join(f"{f}={v}" for f, v in self.data[k].items())
                if op == "HDEL":
                    self._apply(["HDEL", args[1], args[2]])
                    return "OK"
                if op == "DBSIZE":
                    self._cleanup_expired()
                    return str(len(self.data))
                if op == "FLUSHALL":
                    self.data.clear()
                    self.types.clear()
                    self.expires.clear()
                    self._aof_fp.close()
                    open(self.aof_path, "w", encoding="utf-8").close()
                    if os.path.exists(self.snap_path):
                        os.remove(self.snap_path)
                    self._aof_fp = open(self.aof_path, "a", encoding="utf-8")
                    return "OK"
                if op == "SAVE":
                    return self.save_snapshot()
                return f"ERR unknown command {op}"
            except Exception as e:
                return f"ERR {e}"


# ---------- 服务端 ----------
def serve(host, port, db_dir):
    os.makedirs(db_dir, exist_ok=True)
    store = KVStore(os.path.join(db_dir, "kv.aof"),
                    os.path.join(db_dir, "kv.snap"))
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(64)
    print(f"[+] KV server on {host}:{port} (db={db_dir})")

    def handle(conn, addr):
        with conn.makefile("rwb", buffering=0) as fp:
            fp.write(b"WELCOME PyKV/1.0 (type HELP for commands)\n")
            for line in fp:
                line = line.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                if line.upper() in ("QUIT", "EXIT"):
                    fp.write(b"BYE\n")
                    return
                if line.upper() == "HELP":
                    fp.write(b"Commands: SET GET DEL EXISTS KEYS TYPE EXPIRE TTL PERSIST "
                             b"LPUSH RPUSH LRANGE HSET HGET HGETALL HDEL DBSIZE FLUSHALL SAVE PING\n")
                    continue
                args = line.split()
                resp = store.execute(args)
                fp.write(f"{resp}\n".encode("utf-8"))

    try:
        while True:
            conn, addr = srv.accept()
            threading.Thread(target=handle, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[!] shutdown")
    finally:
        srv.close()


# ---------- 客户端 ----------
def client(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    fp = s.makefile("rwb", buffering=0)
    print(fp.readline().decode("utf-8", errors="ignore").rstrip())
    try:
        while True:
            line = input(f"{host}:{port}> ").strip()
            if not line:
                continue
            fp.write((line + "\n").encode("utf-8"))
            if line.upper() in ("QUIT", "EXIT"):
                print(fp.readline().decode("utf-8", errors="ignore").rstrip())
                break
            print(fp.readline().decode("utf-8", errors="ignore").rstrip())
    except (EOFError, KeyboardInterrupt):
        print()
    finally:
        s.close()


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve", help="启动服务端")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=6380)
    s.add_argument("--dir", default="kvdata", help="数据目录")
    c = sub.add_parser("cli", help="交互客户端")
    c.add_argument("--host", default="127.0.0.1")
    c.add_argument("--port", type=int, default=6380)
    sub.add_parser("local", help="本地嵌入式 REPL（无网络）")
    args = p.parse_args()

    if args.cmd == "serve":
        serve(args.host, args.port, args.dir)
    elif args.cmd == "cli":
        client(args.host, args.port)
    elif args.cmd == "local":
        store = KVStore("kv.aof", "kv.snap")
        print("PyKV 本地 REPL (输入 quit 退出)")
        try:
            while True:
                line = input("> ").strip()
                if not line:
                    continue
                if line.lower() in ("quit", "exit"):
                    break
                print(store.execute(line.split()))
        except (EOFError, KeyboardInterrupt):
            print()


if __name__ == "__main__":
    main()
