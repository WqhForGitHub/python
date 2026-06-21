# -*- coding: utf-8 -*-
"""
PyRedis —— 简化版 Redis（纯 Python 标准库实现）

实现要点：
- 基于 socket 的 RESP 协议解析（与真 Redis 客户端 redis-cli 兼容！）
- 单线程事件循环（selectors）+ 命令分派
- 数据结构：String / List / Hash / Set / Sorted Set
- 过期：PEXPIRE / EXPIRE / TTL；惰性删除 + 主动扫描
- 持久化：AOF（每次写命令追加），启动时回放
- 命令子集：
    PING, ECHO, SELECT, FLUSHALL, KEYS, EXISTS, DEL, TYPE
    GET, SET (NX, XX, EX, PX), INCR, INCRBY, DECR, APPEND, STRLEN, MGET, MSET
    EXPIRE, PEXPIRE, TTL, PTTL, PERSIST
    LPUSH, RPUSH, LPOP, RPOP, LLEN, LRANGE, LINDEX
    HSET, HGET, HGETALL, HDEL, HKEYS, HVALS, HLEN, HEXISTS
    SADD, SREM, SISMEMBER, SMEMBERS, SCARD, SINTER, SUNION
    ZADD, ZRANGE, ZSCORE, ZREM, ZCARD, ZRANGEBYSCORE
    DBSIZE, INFO, COMMAND

用法：
    python pyredis.py server [--host=127.0.0.1] [--port=6390] [--aof=dump.aof]
    python pyredis.py cli    [--host=127.0.0.1] [--port=6390]
    python pyredis.py demo
"""
import os
import sys
import time
import socket
import selectors
import threading
import bisect
from collections import defaultdict, deque


# ============================================================
# RESP 协议
# ============================================================
class RESPProtocolError(Exception): pass


class RESPParser:
    """逐字节解析 RESP；返回 list[str|bytes] 或 None（数据不足）"""
    def __init__(self):
        self.buffer = bytearray()

    def feed(self, data: bytes):
        self.buffer.extend(data)

    def parse_one(self):
        """返回 (obj, consumed) 或 (None, 0) 表示数据不够。"""
        if not self.buffer:
            return None, 0
        return self._parse(self.buffer, 0)

    def _readline(self, buf, i):
        end = buf.find(b"\r\n", i)
        if end < 0:
            return None, i
        return bytes(buf[i:end]), end + 2

    def _parse(self, buf, i):
        if i >= len(buf):
            return None, i
        t = chr(buf[i])
        if t in "+-:":
            line, j = self._readline(buf, i + 1)
            if line is None: return None, i
            if t == ":":
                return int(line.decode()), j
            return line.decode(), j
        if t == "$":
            line, j = self._readline(buf, i + 1)
            if line is None: return None, i
            n = int(line)
            if n == -1: return None, j   # 注意：null bulk
            if len(buf) - j < n + 2: return None, i
            data = bytes(buf[j:j + n])
            if buf[j + n:j + n + 2] != b"\r\n":
                raise RESPProtocolError("expected CRLF after bulk")
            return data, j + n + 2
        if t == "*":
            line, j = self._readline(buf, i + 1)
            if line is None: return None, i
            n = int(line)
            if n == -1: return None, j
            arr = []
            for _ in range(n):
                el, j2 = self._parse(buf, j)
                if j2 == j and el is None:
                    return None, i
                arr.append(el)
                j = j2
            return arr, j
        # inline 命令（redis-cli 在某些场景会发） —— 简单处理
        line, j = self._readline(buf, i)
        if line is None: return None, i
        parts = line.split()
        return [p for p in parts], j

    def parse_messages(self):
        out = []
        while True:
            try:
                obj, consumed = self.parse_one()
            except RESPProtocolError:
                self.buffer.clear()
                raise
            if obj is None and consumed == 0:
                break
            del self.buffer[:consumed]
            out.append(obj)
        return out


def encode(obj) -> bytes:
    if obj is None:
        return b"$-1\r\n"
    if isinstance(obj, bool):
        return b":1\r\n" if obj else b":0\r\n"
    if isinstance(obj, int):
        return f":{obj}\r\n".encode()
    if isinstance(obj, float):
        s = format(obj, ".17g")
        return f"${len(s)}\r\n{s}\r\n".encode()
    if isinstance(obj, SimpleString):
        return f"+{obj}\r\n".encode()
    if isinstance(obj, ErrorReply):
        return f"-{obj}\r\n".encode()
    if isinstance(obj, (bytes, bytearray)):
        return b"$" + str(len(obj)).encode() + b"\r\n" + bytes(obj) + b"\r\n"
    if isinstance(obj, str):
        b = obj.encode("utf-8")
        return b"$" + str(len(b)).encode() + b"\r\n" + b + b"\r\n"
    if isinstance(obj, (list, tuple)):
        out = bytearray(b"*" + str(len(obj)).encode() + b"\r\n")
        for x in obj:
            out += encode(x)
        return bytes(out)
    raise TypeError(f"can't encode {type(obj)}")


class SimpleString(str): pass
class ErrorReply(str): pass

OK = SimpleString("OK")
PONG = SimpleString("PONG")


# ============================================================
# 数据库 / 命令实现
# ============================================================
class SortedSet:
    """简化 sorted set：用 dict + sorted list 两套结构。"""
    def __init__(self):
        self.member_score = {}        # member -> score
        self.sorted_pairs = []        # [(score, member)] 已排序

    def add(self, member, score):
        if member in self.member_score:
            old = self.member_score[member]
            self.sorted_pairs.remove((old, member))
        self.member_score[member] = score
        bisect.insort(self.sorted_pairs, (score, member))

    def remove(self, member):
        if member in self.member_score:
            sc = self.member_score.pop(member)
            self.sorted_pairs.remove((sc, member))
            return True
        return False

    def score(self, member):
        return self.member_score.get(member)

    def __len__(self):
        return len(self.member_score)

    def range(self, start, stop):
        n = len(self.sorted_pairs)
        if start < 0: start = max(0, n + start)
        if stop < 0: stop = n + stop
        return [m for _, m in self.sorted_pairs[start:stop + 1]]

    def range_by_score(self, lo, hi):
        return [m for s, m in self.sorted_pairs if lo <= s <= hi]


class Database:
    def __init__(self):
        self.data = {}            # key -> value
        self.expires = {}         # key -> expire_ms (epoch ms)

    def expired(self, key, now_ms):
        ex = self.expires.get(key)
        if ex is not None and now_ms >= ex:
            self.data.pop(key, None)
            self.expires.pop(key, None)
            return True
        return False

    def get(self, key):
        if key in self.data:
            if self.expired(key, _now_ms()):
                return None
            return self.data[key]
        return None

    def set(self, key, value):
        self.data[key] = value

    def delete(self, key):
        self.expires.pop(key, None)
        return self.data.pop(key, _MISSING) is not _MISSING

    def keys_pattern(self, pattern):
        return [k for k in list(self.data.keys()) if _glob_match(pattern, k)]


_MISSING = object()


def _now_ms(): return int(time.time() * 1000)


def _glob_match(pattern, s):
    """简化 glob: * 任意, ? 单字, [abc]"""
    return _gm(pattern, 0, s, 0)


def _gm(pat, i, s, j):
    while i < len(pat):
        c = pat[i]
        if c == "*":
            if i == len(pat) - 1:
                return True
            for k in range(j, len(s) + 1):
                if _gm(pat, i + 1, s, k):
                    return True
            return False
        if j >= len(s): return False
        if c == "?":
            i += 1; j += 1; continue
        if c == "[":
            end = pat.find("]", i)
            if end < 0: return False
            chars = pat[i + 1:end]
            if s[j] not in chars: return False
            i = end + 1; j += 1; continue
        if c != s[j]: return False
        i += 1; j += 1
    return j == len(s)


# ============================================================
# Server
# ============================================================
class PyRedisServer:
    def __init__(self, host="127.0.0.1", port=6390, aof_path=None):
        self.host = host
        self.port = port
        self.aof_path = aof_path
        self.dbs = [Database() for _ in range(16)]
        self.sel = selectors.DefaultSelector()
        self.parsers = {}        # fd -> RESPParser
        self.outbufs = {}        # fd -> bytes
        self.client_db = {}      # fd -> db index
        self.start_time = time.time()
        self.cmd_counter = 0
        self.aof_fh = None
        self._stop = False
        self._cleanup_started = False

        # 把所有 command -> handler
        self.commands = {
            "PING": self.cmd_ping, "ECHO": self.cmd_echo,
            "SELECT": self.cmd_select, "FLUSHALL": self.cmd_flushall,
            "FLUSHDB": self.cmd_flushdb, "KEYS": self.cmd_keys,
            "EXISTS": self.cmd_exists, "DEL": self.cmd_del,
            "TYPE": self.cmd_type, "DBSIZE": self.cmd_dbsize,
            "INFO": self.cmd_info, "COMMAND": self.cmd_command,
            "GET": self.cmd_get, "SET": self.cmd_set,
            "INCR": self.cmd_incr, "INCRBY": self.cmd_incrby,
            "DECR": self.cmd_decr, "APPEND": self.cmd_append,
            "STRLEN": self.cmd_strlen, "MGET": self.cmd_mget, "MSET": self.cmd_mset,
            "EXPIRE": self.cmd_expire, "PEXPIRE": self.cmd_pexpire,
            "TTL": self.cmd_ttl, "PTTL": self.cmd_pttl, "PERSIST": self.cmd_persist,
            "LPUSH": self.cmd_lpush, "RPUSH": self.cmd_rpush,
            "LPOP": self.cmd_lpop, "RPOP": self.cmd_rpop,
            "LLEN": self.cmd_llen, "LRANGE": self.cmd_lrange, "LINDEX": self.cmd_lindex,
            "HSET": self.cmd_hset, "HGET": self.cmd_hget, "HGETALL": self.cmd_hgetall,
            "HDEL": self.cmd_hdel, "HKEYS": self.cmd_hkeys, "HVALS": self.cmd_hvals,
            "HLEN": self.cmd_hlen, "HEXISTS": self.cmd_hexists,
            "SADD": self.cmd_sadd, "SREM": self.cmd_srem,
            "SISMEMBER": self.cmd_sismember, "SMEMBERS": self.cmd_smembers,
            "SCARD": self.cmd_scard, "SINTER": self.cmd_sinter, "SUNION": self.cmd_sunion,
            "ZADD": self.cmd_zadd, "ZRANGE": self.cmd_zrange, "ZSCORE": self.cmd_zscore,
            "ZREM": self.cmd_zrem, "ZCARD": self.cmd_zcard,
            "ZRANGEBYSCORE": self.cmd_zrangebyscore,
            "QUIT": self.cmd_quit,
        }
        self.write_commands = {"SET", "DEL", "INCR", "INCRBY", "DECR", "APPEND",
                               "MSET", "EXPIRE", "PEXPIRE", "PERSIST",
                               "LPUSH", "RPUSH", "LPOP", "RPOP",
                               "HSET", "HDEL", "SADD", "SREM",
                               "ZADD", "ZREM", "FLUSHALL", "FLUSHDB"}

    # ---------- 启动 ----------
    def serve_forever(self):
        if self.aof_path:
            self._aof_load()
            self.aof_fh = open(self.aof_path, "ab")

        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((self.host, self.port))
        srv.listen(128)
        srv.setblocking(False)
        self.sel.register(srv, selectors.EVENT_READ, data="server")
        print(f"[pyredis] listening on {self.host}:{self.port}")

        # 后台过期扫描
        if not self._cleanup_started:
            self._cleanup_started = True
            t = threading.Thread(target=self._expire_loop, daemon=True)
            t.start()

        try:
            while not self._stop:
                events = self.sel.select(timeout=1.0)
                for key, mask in events:
                    if key.data == "server":
                        self._accept(key.fileobj)
                    else:
                        if mask & selectors.EVENT_READ:
                            self._on_read(key.fileobj)
                        if mask & selectors.EVENT_WRITE:
                            self._on_write(key.fileobj)
        finally:
            try:
                srv.close()
            except Exception:
                pass
            if self.aof_fh:
                self.aof_fh.close()

    def _accept(self, srv):
        conn, addr = srv.accept()
        conn.setblocking(False)
        self.parsers[conn.fileno()] = RESPParser()
        self.outbufs[conn.fileno()] = b""
        self.client_db[conn.fileno()] = 0
        self.sel.register(conn, selectors.EVENT_READ, data="client")

    def _on_read(self, conn):
        try:
            data = conn.recv(65536)
        except (ConnectionError, OSError):
            self._close(conn); return
        if not data:
            self._close(conn); return
        fd = conn.fileno()
        parser = self.parsers[fd]
        parser.feed(data)
        try:
            msgs = parser.parse_messages()
        except RESPProtocolError as e:
            self._enqueue(conn, encode(ErrorReply(f"ERR protocol error: {e}")))
            self._close(conn); return
        for m in msgs:
            self._dispatch(conn, m)

    def _on_write(self, conn):
        fd = conn.fileno()
        buf = self.outbufs.get(fd, b"")
        if not buf:
            self.sel.modify(conn, selectors.EVENT_READ, data="client")
            return
        try:
            n = conn.send(buf)
        except (ConnectionError, OSError):
            self._close(conn); return
        self.outbufs[fd] = buf[n:]
        if not self.outbufs[fd]:
            self.sel.modify(conn, selectors.EVENT_READ, data="client")

    def _enqueue(self, conn, data: bytes):
        fd = conn.fileno()
        self.outbufs[fd] = self.outbufs.get(fd, b"") + data
        self.sel.modify(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, data="client")

    def _close(self, conn):
        try:
            self.sel.unregister(conn)
        except Exception:
            pass
        fd = conn.fileno()
        self.parsers.pop(fd, None)
        self.outbufs.pop(fd, None)
        self.client_db.pop(fd, None)
        try:
            conn.close()
        except Exception:
            pass

    def _dispatch(self, conn, args):
        if not args:
            return
        # 全部转 str（除了 ECHO/原样数据）
        cmd = args[0]
        if isinstance(cmd, (bytes, bytearray)):
            cmd = cmd.decode("utf-8", errors="replace")
        cmd = cmd.upper()
        argv = []
        for a in args[1:]:
            if isinstance(a, (bytes, bytearray)):
                argv.append(a.decode("utf-8", errors="replace"))
            else:
                argv.append(str(a))
        handler = self.commands.get(cmd)
        if not handler:
            self._enqueue(conn, encode(ErrorReply(f"ERR unknown command '{cmd}'")))
            return
        self.cmd_counter += 1
        try:
            reply = handler(conn, argv)
        except _ReplyError as e:
            self._enqueue(conn, encode(ErrorReply(str(e))))
            return
        except Exception as e:
            self._enqueue(conn, encode(ErrorReply(f"ERR {e}")))
            return
        if reply is _NO_REPLY:
            return
        self._enqueue(conn, encode(reply))

        if cmd in self.write_commands and self.aof_fh:
            self._aof_append([cmd, *argv])

    # ---------- AOF ----------
    def _aof_append(self, args):
        line = "*" + str(len(args)) + "\r\n"
        for a in args:
            b = a.encode("utf-8") if isinstance(a, str) else a
            line += "$" + str(len(b)) + "\r\n"
            line = line.encode("utf-8") if isinstance(line, str) else line
            self.aof_fh.write(line)
            self.aof_fh.write(b)
            self.aof_fh.write(b"\r\n")
            line = ""
        if line:
            self.aof_fh.write(line.encode("utf-8") if isinstance(line, str) else line)
        self.aof_fh.flush()

    def _aof_load(self):
        if not os.path.exists(self.aof_path):
            return
        with open(self.aof_path, "rb") as f:
            data = f.read()
        parser = RESPParser()
        parser.feed(data)
        try:
            msgs = parser.parse_messages()
        except Exception as e:
            print(f"[pyredis] AOF parse error: {e}")
            return
        n = 0
        # 模拟一个虚拟 client
        class _Stub:
            def __init__(s): s.fno = -1
            def fileno(s): return s.fno
        stub = _Stub()
        self.client_db[-1] = 0
        for m in msgs:
            try:
                argv_full = [a.decode() if isinstance(a, (bytes, bytearray)) else str(a) for a in m]
                cmd = argv_full[0].upper()
                handler = self.commands.get(cmd)
                if handler:
                    handler(stub, argv_full[1:])
                    n += 1
            except Exception:
                pass
        print(f"[pyredis] AOF replayed {n} commands")

    # ---------- 后台过期扫描 ----------
    def _expire_loop(self):
        while not self._stop:
            time.sleep(0.1)
            now = _now_ms()
            for db in self.dbs:
                # 随机抽样 20 个待检查
                keys = list(db.expires.keys())[:20]
                for k in keys:
                    db.expired(k, now)

    # ---------- 工具 ----------
    def _db(self, conn):
        return self.dbs[self.client_db.get(conn.fileno(), 0)]

    # ============================================================
    # 命令实现
    # ============================================================
    # ---- 连接 ----
    def cmd_ping(self, c, a):
        return PONG if not a else a[0]

    def cmd_echo(self, c, a):
        if len(a) != 1: raise _ReplyError("ERR wrong number of arguments for 'ECHO'")
        return a[0]

    def cmd_quit(self, c, a):
        self._enqueue(c, encode(OK))
        self._close(c)
        return _NO_REPLY

    def cmd_select(self, c, a):
        if len(a) != 1: raise _ReplyError("ERR wrong arg count")
        i = int(a[0])
        if not 0 <= i < len(self.dbs): raise _ReplyError("ERR DB index out of range")
        self.client_db[c.fileno()] = i
        return OK

    # ---- 通用 ----
    def cmd_flushall(self, c, a):
        for db in self.dbs:
            db.data.clear(); db.expires.clear()
        return OK

    def cmd_flushdb(self, c, a):
        db = self._db(c); db.data.clear(); db.expires.clear()
        return OK

    def cmd_keys(self, c, a):
        if len(a) != 1: raise _ReplyError("ERR wrong arg count")
        return self._db(c).keys_pattern(a[0])

    def cmd_exists(self, c, a):
        db = self._db(c); now = _now_ms()
        return sum(1 for k in a if not db.expired(k, now) and k in db.data)

    def cmd_del(self, c, a):
        db = self._db(c)
        return sum(1 for k in a if db.delete(k))

    def cmd_type(self, c, a):
        db = self._db(c)
        v = db.get(a[0])
        if v is None: return SimpleString("none")
        if isinstance(v, (str, bytes, bytearray, int, float)): return SimpleString("string")
        if isinstance(v, deque): return SimpleString("list")
        if isinstance(v, dict): return SimpleString("hash")
        if isinstance(v, set): return SimpleString("set")
        if isinstance(v, SortedSet): return SimpleString("zset")
        return SimpleString("unknown")

    def cmd_dbsize(self, c, a):
        return len(self._db(c).data)

    def cmd_info(self, c, a):
        up = int(time.time() - self.start_time)
        text = (f"# Server\nredis_version:py-0.1\nuptime_in_seconds:{up}\n"
                f"# Stats\ntotal_commands_processed:{self.cmd_counter}\n"
                f"# Keyspace\ndb0:keys={len(self.dbs[0].data)}\n")
        return text

    def cmd_command(self, c, a):
        return [k for k in self.commands.keys()]

    # ---- String ----
    def cmd_get(self, c, a):
        v = self._db(c).get(a[0])
        if v is None: return None
        if isinstance(v, (deque, dict, set, SortedSet)):
            raise _ReplyError("WRONGTYPE Operation against a key holding the wrong kind of value")
        return v if isinstance(v, (str, bytes)) else str(v)

    def cmd_set(self, c, a):
        if len(a) < 2: raise _ReplyError("ERR wrong arg count")
        key, val = a[0], a[1]
        nx = xx = False
        ex_ms = None
        i = 2
        while i < len(a):
            opt = a[i].upper()
            if opt == "NX": nx = True; i += 1
            elif opt == "XX": xx = True; i += 1
            elif opt == "EX": ex_ms = int(a[i + 1]) * 1000; i += 2
            elif opt == "PX": ex_ms = int(a[i + 1]); i += 2
            else: raise _ReplyError(f"ERR syntax error near '{opt}'")
        db = self._db(c)
        exists = db.get(key) is not None
        if nx and exists: return None
        if xx and not exists: return None
        db.set(key, val)
        if ex_ms is not None:
            db.expires[key] = _now_ms() + ex_ms
        else:
            db.expires.pop(key, None)
        return OK

    def cmd_incr(self, c, a): return self._incrby(c, a[0], 1)
    def cmd_decr(self, c, a): return self._incrby(c, a[0], -1)

    def cmd_incrby(self, c, a):
        return self._incrby(c, a[0], int(a[1]))

    def _incrby(self, c, key, by):
        db = self._db(c)
        v = db.get(key)
        if v is None:
            n = 0
        else:
            try:
                n = int(v)
            except (ValueError, TypeError):
                raise _ReplyError("ERR value is not an integer or out of range")
        n += by
        db.set(key, str(n))
        return n

    def cmd_append(self, c, a):
        db = self._db(c)
        v = db.get(a[0]) or ""
        if isinstance(v, bytes): v = v.decode("utf-8", errors="replace")
        new = v + a[1]
        db.set(a[0], new)
        return len(new)

    def cmd_strlen(self, c, a):
        v = self._db(c).get(a[0]) or ""
        if isinstance(v, bytes): return len(v)
        return len(str(v))

    def cmd_mget(self, c, a):
        return [self.cmd_get(c, [k]) for k in a]

    def cmd_mset(self, c, a):
        if len(a) % 2: raise _ReplyError("ERR wrong arg count")
        db = self._db(c)
        for i in range(0, len(a), 2):
            db.set(a[i], a[i + 1])
            db.expires.pop(a[i], None)
        return OK

    # ---- 过期 ----
    def cmd_expire(self, c, a):
        return self._expire(c, a[0], int(a[1]) * 1000)

    def cmd_pexpire(self, c, a):
        return self._expire(c, a[0], int(a[1]))

    def _expire(self, c, key, ms):
        db = self._db(c)
        if db.get(key) is None: return 0
        db.expires[key] = _now_ms() + ms
        return 1

    def cmd_ttl(self, c, a):
        db = self._db(c)
        if db.get(a[0]) is None: return -2
        ex = db.expires.get(a[0])
        if ex is None: return -1
        return max(0, (ex - _now_ms()) // 1000)

    def cmd_pttl(self, c, a):
        db = self._db(c)
        if db.get(a[0]) is None: return -2
        ex = db.expires.get(a[0])
        if ex is None: return -1
        return max(0, ex - _now_ms())

    def cmd_persist(self, c, a):
        db = self._db(c)
        if a[0] in db.expires:
            del db.expires[a[0]]
            return 1
        return 0

    # ---- List ----
    def _list(self, db, key, create=False):
        v = db.get(key)
        if v is None:
            if create:
                v = deque(); db.set(key, v); return v
            return None
        if not isinstance(v, deque):
            raise _ReplyError("WRONGTYPE Operation against a key holding the wrong kind of value")
        return v

    def cmd_lpush(self, c, a):
        db = self._db(c); lst = self._list(db, a[0], create=True)
        for x in a[1:]: lst.appendleft(x)
        return len(lst)

    def cmd_rpush(self, c, a):
        db = self._db(c); lst = self._list(db, a[0], create=True)
        for x in a[1:]: lst.append(x)
        return len(lst)

    def cmd_lpop(self, c, a):
        lst = self._list(self._db(c), a[0])
        if not lst: return None
        v = lst.popleft()
        if not lst: self._db(c).delete(a[0])
        return v

    def cmd_rpop(self, c, a):
        lst = self._list(self._db(c), a[0])
        if not lst: return None
        v = lst.pop()
        if not lst: self._db(c).delete(a[0])
        return v

    def cmd_llen(self, c, a):
        lst = self._list(self._db(c), a[0])
        return len(lst) if lst else 0

    def cmd_lrange(self, c, a):
        lst = self._list(self._db(c), a[0])
        if not lst: return []
        n = len(lst); s = int(a[1]); e = int(a[2])
        if s < 0: s = max(0, n + s)
        if e < 0: e = n + e
        return list(lst)[s:e + 1]

    def cmd_lindex(self, c, a):
        lst = self._list(self._db(c), a[0])
        if not lst: return None
        i = int(a[1]); n = len(lst)
        if i < 0: i = n + i
        if 0 <= i < n: return list(lst)[i]
        return None

    # ---- Hash ----
    def _hash(self, db, key, create=False):
        v = db.get(key)
        if v is None:
            if create: v = {}; db.set(key, v); return v
            return None
        if not isinstance(v, dict):
            raise _ReplyError("WRONGTYPE")
        return v

    def cmd_hset(self, c, a):
        if len(a) < 3 or len(a) % 2 == 0: raise _ReplyError("ERR wrong arg count")
        h = self._hash(self._db(c), a[0], create=True)
        added = 0
        for i in range(1, len(a), 2):
            if a[i] not in h: added += 1
            h[a[i]] = a[i + 1]
        return added

    def cmd_hget(self, c, a):
        h = self._hash(self._db(c), a[0]); return h.get(a[1]) if h else None

    def cmd_hgetall(self, c, a):
        h = self._hash(self._db(c), a[0])
        if not h: return []
        out = []
        for k, v in h.items():
            out.append(k); out.append(v)
        return out

    def cmd_hdel(self, c, a):
        h = self._hash(self._db(c), a[0])
        if not h: return 0
        n = 0
        for k in a[1:]:
            if k in h:
                del h[k]; n += 1
        if not h: self._db(c).delete(a[0])
        return n

    def cmd_hkeys(self, c, a):
        h = self._hash(self._db(c), a[0]); return list(h.keys()) if h else []

    def cmd_hvals(self, c, a):
        h = self._hash(self._db(c), a[0]); return list(h.values()) if h else []

    def cmd_hlen(self, c, a):
        h = self._hash(self._db(c), a[0]); return len(h) if h else 0

    def cmd_hexists(self, c, a):
        h = self._hash(self._db(c), a[0]); return 1 if h and a[1] in h else 0

    # ---- Set ----
    def _set(self, db, key, create=False):
        v = db.get(key)
        if v is None:
            if create: v = set(); db.set(key, v); return v
            return None
        if not isinstance(v, set):
            raise _ReplyError("WRONGTYPE")
        return v

    def cmd_sadd(self, c, a):
        s = self._set(self._db(c), a[0], create=True); n = 0
        for m in a[1:]:
            if m not in s: s.add(m); n += 1
        return n

    def cmd_srem(self, c, a):
        s = self._set(self._db(c), a[0]); n = 0
        if not s: return 0
        for m in a[1:]:
            if m in s: s.remove(m); n += 1
        if not s: self._db(c).delete(a[0])
        return n

    def cmd_sismember(self, c, a):
        s = self._set(self._db(c), a[0])
        return 1 if s and a[1] in s else 0

    def cmd_smembers(self, c, a):
        s = self._set(self._db(c), a[0]); return list(s) if s else []

    def cmd_scard(self, c, a):
        s = self._set(self._db(c), a[0]); return len(s) if s else 0

    def cmd_sinter(self, c, a):
        sets = [self._set(self._db(c), k) or set() for k in a]
        if not sets: return []
        return list(set.intersection(*sets))

    def cmd_sunion(self, c, a):
        sets = [self._set(self._db(c), k) or set() for k in a]
        if not sets: return []
        return list(set.union(*sets))

    # ---- Sorted Set ----
    def _zset(self, db, key, create=False):
        v = db.get(key)
        if v is None:
            if create: v = SortedSet(); db.set(key, v); return v
            return None
        if not isinstance(v, SortedSet):
            raise _ReplyError("WRONGTYPE")
        return v

    def cmd_zadd(self, c, a):
        z = self._zset(self._db(c), a[0], create=True); n = 0
        i = 1
        while i + 1 < len(a):
            score = float(a[i]); member = a[i + 1]
            if member not in z.member_score:
                n += 1
            z.add(member, score)
            i += 2
        return n

    def cmd_zrange(self, c, a):
        z = self._zset(self._db(c), a[0])
        if not z: return []
        return z.range(int(a[1]), int(a[2]))

    def cmd_zscore(self, c, a):
        z = self._zset(self._db(c), a[0])
        if not z: return None
        s = z.score(a[1])
        if s is None: return None
        return format(s, ".17g")

    def cmd_zrem(self, c, a):
        z = self._zset(self._db(c), a[0])
        if not z: return 0
        n = sum(1 for m in a[1:] if z.remove(m))
        if len(z) == 0: self._db(c).delete(a[0])
        return n

    def cmd_zcard(self, c, a):
        z = self._zset(self._db(c), a[0]); return len(z) if z else 0

    def cmd_zrangebyscore(self, c, a):
        z = self._zset(self._db(c), a[0])
        if not z: return []
        return z.range_by_score(float(a[1]), float(a[2]))


_NO_REPLY = object()


class _ReplyError(Exception): pass


# ============================================================
# Mini CLI
# ============================================================
class CLI:
    def __init__(self, host="127.0.0.1", port=6390):
        self.host = host; self.port = port
        self.sock = None
        self.parser = RESPParser()

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

    def close(self):
        try: self.sock.close()
        except: pass

    def call(self, *args):
        msg = encode(list(args))
        self.sock.sendall(msg)
        while True:
            chunk = self.sock.recv(65536)
            if not chunk:
                return None
            self.parser.feed(chunk)
            obj, n = self.parser.parse_one()
            if n > 0:
                del self.parser.buffer[:n]
                return obj

    def repl(self):
        self.connect()
        print(f"connected to {self.host}:{self.port}")
        while True:
            try:
                line = input(f"{self.host}:{self.port}> ")
            except EOFError:
                break
            if not line.strip(): continue
            parts = line.split()
            try:
                r = self.call(*parts)
            except Exception as e:
                print(f"(err) {e}"); break
            print(_format_reply(r))
        self.close()


def _format_reply(r, indent=""):
    if r is None: return "(nil)"
    if isinstance(r, ErrorReply): return f"(error) {r}"
    if isinstance(r, SimpleString): return r
    if isinstance(r, bool): return "1" if r else "0"
    if isinstance(r, int): return f"(integer) {r}"
    if isinstance(r, (bytes, bytearray)):
        try: return r.decode("utf-8")
        except: return repr(r)
    if isinstance(r, list):
        if not r: return "(empty list)"
        return "\n".join(f"{indent}{i+1}) {_format_reply(x, indent + '   ')}" for i, x in enumerate(r))
    return str(r)


# ============================================================
# Demo（同进程跑 server + client）
# ============================================================
def cmd_demo():
    port = 6391
    server = PyRedisServer(host="127.0.0.1", port=port)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.3)

    cli = CLI(port=port); cli.connect()
    print("\n=== PyRedis Demo ===")
    cases = [
        ("PING",),
        ("SET", "name", "alice"),
        ("GET", "name"),
        ("INCR", "counter"),
        ("INCRBY", "counter", "10"),
        ("RPUSH", "list", "a", "b", "c"),
        ("LRANGE", "list", "0", "-1"),
        ("HSET", "user:1", "name", "bob", "age", "30"),
        ("HGETALL", "user:1"),
        ("SADD", "tags", "py", "rust", "go"),
        ("SMEMBERS", "tags"),
        ("ZADD", "score", "10", "tom", "20", "jerry", "5", "spike"),
        ("ZRANGE", "score", "0", "-1"),
        ("ZRANGEBYSCORE", "score", "0", "15"),
        ("KEYS", "*"),
        ("DBSIZE",),
    ]
    for c in cases:
        r = cli.call(*c)
        print(f"> {' '.join(c)}\n  {_format_reply(r)}")
    cli.close()
    server._stop = True
    print("\n[demo] done.")


def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    cmd = sys.argv[1]
    if cmd == "server":
        host, port, aof = "127.0.0.1", 6390, None
        for a in sys.argv[2:]:
            if a.startswith("--host="): host = a.split("=", 1)[1]
            elif a.startswith("--port="): port = int(a.split("=", 1)[1])
            elif a.startswith("--aof="): aof = a.split("=", 1)[1]
        PyRedisServer(host=host, port=port, aof_path=aof).serve_forever()
    elif cmd == "cli":
        host, port = "127.0.0.1", 6390
        for a in sys.argv[2:]:
            if a.startswith("--host="): host = a.split("=", 1)[1]
            elif a.startswith("--port="): port = int(a.split("=", 1)[1])
        CLI(host=host, port=port).repl()
    elif cmd == "demo":
        cmd_demo()
    else:
        print("unknown command:", cmd)


if __name__ == "__main__":
    main()
