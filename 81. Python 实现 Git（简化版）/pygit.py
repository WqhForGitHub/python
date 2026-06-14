# -*- coding: utf-8 -*-
"""
PyGit —— 简化版 Git（纯 Python 标准库实现）

实现了 Git 的核心模型：
    - blob / tree / commit 三类对象
    - 内容寻址存储：obj_id = sha1(header + body)
    - 对象 zlib 压缩
    - .pygit/objects/<2>/<38> 存储布局
    - 索引（暂存区）：.pygit/index 简易二进制
    - 引用：.pygit/HEAD、.pygit/refs/heads/<branch>
    - 命令：init, add, status, commit, log, branch, checkout, diff, cat-file, ls-tree

对象格式（与 Git 完全相同）：
    blob:    "blob <size>\\0<content>"
    tree:    "tree <size>\\0[<mode> <name>\\0<20-byte sha1>]*"
    commit:  "commit <size>\\0tree <sha>\\nparent <sha>\\n...\\n\\n<msg>"

注：本实现的索引格式 / 配置是简化版，但对象格式与 Git 兼容（同一文件 hash 一致）。

用法：
    python pygit.py init
    python pygit.py add <file>...
    python pygit.py status
    python pygit.py commit -m "msg"
    python pygit.py log
    python pygit.py branch [name]
    python pygit.py checkout <name>
    python pygit.py diff
    python pygit.py cat-file <oid>
    python pygit.py ls-tree <oid>
    python pygit.py demo            # 创建临时仓库做完整演示
"""
import os
import sys
import zlib
import hashlib
import time
import struct
import shutil
import difflib
import tempfile
from typing import Optional, List, Tuple, Dict


GIT_DIR = ".pygit"


# ============================================================
# Repository
# ============================================================
class Repo:
    def __init__(self, root):
        self.root = os.path.abspath(root)
        self.gitdir = os.path.join(self.root, GIT_DIR)

    @classmethod
    def find(cls):
        cur = os.getcwd()
        while True:
            if os.path.isdir(os.path.join(cur, GIT_DIR)):
                return cls(cur)
            p = os.path.dirname(cur)
            if p == cur:
                raise SystemExit("fatal: not a pygit repository (or any parent)")
            cur = p

    # ------- 对象存储 -------
    def hash_object(self, kind: str, body: bytes, write=True) -> str:
        header = f"{kind} {len(body)}".encode() + b"\0"
        full = header + body
        oid = hashlib.sha1(full).hexdigest()
        if write:
            d = os.path.join(self.gitdir, "objects", oid[:2])
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, oid[2:])
            if not os.path.exists(p):
                with open(p, "wb") as f:
                    f.write(zlib.compress(full))
        return oid

    def read_object(self, oid: str) -> Tuple[str, bytes]:
        p = os.path.join(self.gitdir, "objects", oid[:2], oid[2:])
        with open(p, "rb") as f:
            raw = zlib.decompress(f.read())
        nul = raw.index(b"\0")
        head = raw[:nul].decode()
        kind, _ = head.split(" ", 1)
        return kind, raw[nul + 1:]

    def object_exists(self, oid):
        return os.path.exists(os.path.join(self.gitdir, "objects", oid[:2], oid[2:]))

    # ------- 引用 -------
    def head_ref(self) -> Tuple[str, Optional[str]]:
        """返回 (ref_path, oid)。ref_path 为 'refs/heads/master' 或裸 oid（detached）。"""
        with open(os.path.join(self.gitdir, "HEAD"), "r", encoding="utf-8") as f:
            data = f.read().strip()
        if data.startswith("ref: "):
            ref = data[5:]
            return ref, self.read_ref(ref)
        return data, data

    def read_ref(self, ref) -> Optional[str]:
        p = os.path.join(self.gitdir, ref)
        if not os.path.exists(p): return None
        with open(p, "r", encoding="utf-8") as f:
            return f.read().strip()

    def write_ref(self, ref, oid):
        p = os.path.join(self.gitdir, ref)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(oid + "\n")

    def update_head(self, ref_or_oid):
        with open(os.path.join(self.gitdir, "HEAD"), "w", encoding="utf-8") as f:
            if "/" in ref_or_oid:
                f.write(f"ref: {ref_or_oid}\n")
            else:
                f.write(ref_or_oid + "\n")

    def list_branches(self):
        d = os.path.join(self.gitdir, "refs", "heads")
        if not os.path.isdir(d): return []
        return sorted(os.listdir(d))

    def current_branch(self) -> Optional[str]:
        ref, _ = self.head_ref()
        if ref.startswith("refs/heads/"):
            return ref[len("refs/heads/"):]
        return None

    # ------- 索引（暂存区） -------
    # 格式：[4字节count][repeat: [4字节name_len][name utf-8][20字节sha1]]
    def read_index(self) -> Dict[str, str]:
        p = os.path.join(self.gitdir, "index")
        if not os.path.exists(p): return {}
        with open(p, "rb") as f:
            data = f.read()
        i = 0
        (count,) = struct.unpack(">I", data[i:i + 4]); i += 4
        out = {}
        for _ in range(count):
            (nl,) = struct.unpack(">I", data[i:i + 4]); i += 4
            name = data[i:i + nl].decode("utf-8"); i += nl
            sha = data[i:i + 20].hex(); i += 20
            out[name] = sha
        return out

    def write_index(self, idx: Dict[str, str]):
        out = struct.pack(">I", len(idx))
        for name in sorted(idx.keys()):
            nb = name.encode("utf-8")
            out += struct.pack(">I", len(nb)) + nb + bytes.fromhex(idx[name])
        with open(os.path.join(self.gitdir, "index"), "wb") as f:
            f.write(out)


# ============================================================
# 对象操作
# ============================================================
def write_blob_from_file(repo: Repo, path: str) -> str:
    with open(path, "rb") as f:
        data = f.read()
    return repo.hash_object("blob", data)


def build_tree(repo: Repo, index: Dict[str, str]) -> str:
    """把扁平的 path->blob_oid 索引构建成嵌套 tree。返回根 tree oid。"""
    # 按目录分组
    root = {"_files": {}, "_dirs": {}}
    for path, oid in index.items():
        parts = path.replace("\\", "/").split("/")
        node = root
        for p in parts[:-1]:
            node = node["_dirs"].setdefault(p, {"_files": {}, "_dirs": {}})
        node["_files"][parts[-1]] = oid

    def write(node) -> str:
        entries = []
        for name, oid in node["_files"].items():
            entries.append(("100644", name, oid))
        for name, sub in node["_dirs"].items():
            sub_oid = write(sub)
            entries.append(("40000", name, sub_oid))
        entries.sort(key=lambda e: e[1])
        body = b""
        for mode, name, oid in entries:
            body += f"{mode} {name}".encode() + b"\0" + bytes.fromhex(oid)
        return repo.hash_object("tree", body)

    return write(root)


def parse_tree(body: bytes):
    """yield (mode, name, oid)"""
    i = 0
    while i < len(body):
        sp = body.index(b" ", i)
        mode = body[i:sp].decode(); i = sp + 1
        nul = body.index(b"\0", i)
        name = body[i:nul].decode("utf-8"); i = nul + 1
        oid = body[i:i + 20].hex(); i += 20
        yield mode, name, oid


def flatten_tree(repo: Repo, tree_oid: str, prefix="") -> Dict[str, str]:
    out = {}
    kind, body = repo.read_object(tree_oid)
    assert kind == "tree"
    for mode, name, oid in parse_tree(body):
        path = (prefix + "/" + name).lstrip("/")
        if mode == "40000":
            out.update(flatten_tree(repo, oid, path))
        else:
            out[path] = oid
    return out


def make_commit(repo: Repo, tree_oid: str, parents: List[str],
                msg: str, author="pygit <pygit@example.com>") -> str:
    ts = int(time.time())
    tz = "+0000"
    lines = [f"tree {tree_oid}"]
    for p in parents:
        lines.append(f"parent {p}")
    lines.append(f"author {author} {ts} {tz}")
    lines.append(f"committer {author} {ts} {tz}")
    lines.append("")
    lines.append(msg)
    body = "\n".join(lines).encode("utf-8") + b"\n"
    return repo.hash_object("commit", body)


def parse_commit(body: bytes):
    text = body.decode("utf-8", errors="replace")
    head, _, msg = text.partition("\n\n")
    info = {"parents": []}
    for line in head.splitlines():
        if not line: continue
        k, _, v = line.partition(" ")
        if k == "parent": info["parents"].append(v)
        else: info[k] = v
    info["message"] = msg.rstrip("\n")
    return info


# ============================================================
# 工作树扫描
# ============================================================
IGNORED_DIRS = {".pygit", ".git", "__pycache__", ".idea", ".vscode"}


def scan_worktree(root) -> List[str]:
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]
        for fn in filenames:
            if fn.startswith("."): continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace("\\", "/")
            out.append(rel)
    return sorted(out)


# ============================================================
# 命令
# ============================================================
def cmd_init(args):
    root = os.getcwd()
    g = os.path.join(root, GIT_DIR)
    if os.path.exists(g):
        print(f"reinitialized existing pygit repository in {g}")
    else:
        os.makedirs(os.path.join(g, "objects"))
        os.makedirs(os.path.join(g, "refs", "heads"))
        with open(os.path.join(g, "HEAD"), "w", encoding="utf-8") as f:
            f.write("ref: refs/heads/master\n")
        print(f"initialized empty pygit repository in {g}")


def cmd_add(args):
    if not args:
        print("usage: add <file>..."); return
    repo = Repo.find()
    idx = repo.read_index()
    files = []
    for a in args:
        full = os.path.abspath(a)
        if os.path.isdir(full):
            for fp in scan_worktree(full):
                files.append(os.path.relpath(os.path.join(full, fp), repo.root).replace("\\", "/"))
        else:
            files.append(os.path.relpath(full, repo.root).replace("\\", "/"))
    for rel in files:
        full = os.path.join(repo.root, rel)
        if not os.path.exists(full):
            # 删除暂存
            idx.pop(rel, None)
            continue
        oid = write_blob_from_file(repo, full)
        idx[rel] = oid
        print(f"  add {rel}  {oid[:8]}")
    repo.write_index(idx)


def cmd_status(args):
    repo = Repo.find()
    idx = repo.read_index()

    head_ref, head_oid = repo.head_ref()
    head_files = {}
    if head_oid:
        kind, body = repo.read_object(head_oid)
        if kind == "commit":
            ci = parse_commit(body)
            head_files = flatten_tree(repo, ci["tree"])

    wt = set(scan_worktree(repo.root))

    # staged: idx 与 head_files 对比
    staged_new = sorted(set(idx) - set(head_files))
    staged_mod = sorted(p for p in set(idx) & set(head_files) if idx[p] != head_files[p])
    staged_del = sorted(set(head_files) - set(idx))

    # unstaged: wt 与 idx 对比
    unstaged_mod = []
    untracked = []
    for p in sorted(wt):
        if p not in idx:
            untracked.append(p); continue
        full = os.path.join(repo.root, p)
        with open(full, "rb") as f:
            data = f.read()
        oid = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        if oid != idx[p]:
            unstaged_mod.append(p)
    deleted = sorted(set(idx) - wt)

    branch = repo.current_branch() or "(detached)"
    print(f"On branch {branch}")
    if head_oid is None:
        print("\nNo commits yet")
    if staged_new or staged_mod or staged_del:
        print("\nChanges to be committed:")
        for p in staged_new: print(f"  new file:   {p}")
        for p in staged_mod: print(f"  modified:   {p}")
        for p in staged_del: print(f"  deleted:    {p}")
    if unstaged_mod or deleted:
        print("\nChanges not staged for commit:")
        for p in unstaged_mod: print(f"  modified:   {p}")
        for p in deleted:      print(f"  deleted:    {p}")
    if untracked:
        print("\nUntracked files:")
        for p in untracked: print(f"  {p}")
    if not (staged_new or staged_mod or staged_del or unstaged_mod or deleted or untracked):
        print("\nnothing to commit, working tree clean")


def cmd_commit(args):
    msg = None
    i = 0
    while i < len(args):
        if args[i] == "-m":
            msg = args[i + 1]; i += 2
        else:
            i += 1
    if not msg:
        print("usage: commit -m \"message\""); return
    repo = Repo.find()
    idx = repo.read_index()
    if not idx:
        print("nothing to commit (index empty)"); return
    tree_oid = build_tree(repo, idx)
    head_ref, head_oid = repo.head_ref()
    parents = [head_oid] if head_oid else []
    commit_oid = make_commit(repo, tree_oid, parents, msg)
    if head_ref.startswith("refs/heads/"):
        repo.write_ref(head_ref, commit_oid)
    else:
        repo.update_head(commit_oid)
    print(f"[{repo.current_branch() or 'detached'} {commit_oid[:8]}] {msg}")


def cmd_log(args):
    repo = Repo.find()
    _, oid = repo.head_ref()
    if not oid:
        print("(no commits)"); return
    while oid:
        kind, body = repo.read_object(oid)
        info = parse_commit(body)
        print(f"commit {oid}")
        if "author" in info: print(f"Author: {info['author']}")
        print()
        for line in info["message"].splitlines():
            print(f"    {line}")
        print()
        if not info["parents"]: break
        oid = info["parents"][0]


def cmd_branch(args):
    repo = Repo.find()
    if not args:
        cur = repo.current_branch()
        for b in repo.list_branches():
            mark = "*" if b == cur else " "
            print(f"{mark} {b}")
        return
    name = args[0]
    _, head_oid = repo.head_ref()
    if not head_oid:
        print("fatal: cannot create branch, no commits yet"); return
    repo.write_ref(f"refs/heads/{name}", head_oid)
    print(f"created branch {name}")


def cmd_checkout(args):
    if not args:
        print("usage: checkout <branch>"); return
    name = args[0]
    repo = Repo.find()
    branches = repo.list_branches()
    if name in branches:
        ref = f"refs/heads/{name}"
        oid = repo.read_ref(ref)
    elif repo.object_exists(name):
        ref = name; oid = name
    else:
        print(f"error: branch/oid '{name}' not found"); return

    # 取目标 commit 的 tree 文件
    kind, body = repo.read_object(oid)
    ci = parse_commit(body)
    target = flatten_tree(repo, ci["tree"])

    # 删除当前已跟踪文件，然后写入目标
    cur_idx = repo.read_index()
    for p in list(cur_idx.keys()):
        full = os.path.join(repo.root, p)
        if os.path.exists(full):
            try: os.remove(full)
            except OSError: pass
    for p, oid_ in target.items():
        full = os.path.join(repo.root, p)
        os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
        kind2, data = repo.read_object(oid_)
        with open(full, "wb") as f:
            f.write(data)
    repo.write_index(target)
    if ref.startswith("refs/heads/"):
        repo.update_head(ref)
    else:
        repo.update_head(oid)
    print(f"switched to {name}")


def cmd_diff(args):
    """对比 index 与工作树。"""
    repo = Repo.find()
    idx = repo.read_index()
    for p in sorted(idx):
        full = os.path.join(repo.root, p)
        if not os.path.exists(full): continue
        with open(full, "rb") as f:
            new = f.read()
        kind, old = repo.read_object(idx[p])
        if old == new: continue
        try:
            old_t = old.decode("utf-8")
            new_t = new.decode("utf-8")
        except UnicodeDecodeError:
            print(f"--- {p}\n+++ {p}\n(binary)\n"); continue
        diff = difflib.unified_diff(
            old_t.splitlines(keepends=False),
            new_t.splitlines(keepends=False),
            fromfile=f"a/{p}", tofile=f"b/{p}", lineterm="",
        )
        print("\n".join(diff))


def cmd_cat_file(args):
    if not args:
        print("usage: cat-file <oid>"); return
    repo = Repo.find()
    kind, body = repo.read_object(args[0])
    if kind == "tree":
        for mode, name, oid in parse_tree(body):
            print(f"{mode}  {oid}  {name}")
    elif kind == "commit":
        print(body.decode("utf-8", errors="replace"))
    else:
        try: sys.stdout.write(body.decode("utf-8"))
        except UnicodeDecodeError: sys.stdout.buffer.write(body)


def cmd_ls_tree(args):
    if not args:
        print("usage: ls-tree <oid>"); return
    repo = Repo.find()
    kind, body = repo.read_object(args[0])
    if kind == "commit":
        ci = parse_commit(body)
        oid = ci["tree"]
        kind, body = repo.read_object(oid)
    if kind != "tree":
        print(f"not a tree: {args[0]}"); return
    for mode, name, oid in parse_tree(body):
        kind = "tree" if mode == "40000" else "blob"
        print(f"{mode}  {kind}  {oid}  {name}")


def cmd_demo(args):
    """在临时目录里把全流程跑一遍。"""
    work = tempfile.mkdtemp(prefix="pygit_demo_")
    print(f"[demo] workdir: {work}\n")
    old = os.getcwd()
    try:
        os.chdir(work)
        cmd_init([])
        with open("hello.txt", "w", encoding="utf-8") as f:
            f.write("hello world\n")
        with open("note.md", "w", encoding="utf-8") as f:
            f.write("# Note\n\nfirst line\n")

        print("\n--- add ---")
        cmd_add(["hello.txt", "note.md"])
        print("\n--- status ---")
        cmd_status([])
        print("\n--- commit ---")
        cmd_commit(["-m", "init"])

        # 改一个文件
        with open("note.md", "a", encoding="utf-8") as f:
            f.write("second line\n")

        print("\n--- diff (before add) ---")
        cmd_diff([])

        print("\n--- branch dev ---")
        cmd_branch(["dev"])
        print("\n--- branch list ---")
        cmd_branch([])

        print("\n--- add note.md & commit on master ---")
        cmd_add(["note.md"])
        cmd_commit(["-m", "extend note"])

        print("\n--- log ---")
        cmd_log([])

        print("\n--- checkout dev ---")
        cmd_checkout(["dev"])
        with open("note.md", "r", encoding="utf-8") as f:
            print("note.md on dev:\n" + f.read())

        print("--- back to master ---")
        cmd_checkout(["master"])
        with open("note.md", "r", encoding="utf-8") as f:
            print("note.md on master:\n" + f.read())
    finally:
        os.chdir(old)
        shutil.rmtree(work, ignore_errors=True)


# ============================================================
# main
# ============================================================
COMMANDS = {
    "init": cmd_init, "add": cmd_add, "status": cmd_status,
    "commit": cmd_commit, "log": cmd_log, "branch": cmd_branch,
    "checkout": cmd_checkout, "diff": cmd_diff,
    "cat-file": cmd_cat_file, "ls-tree": cmd_ls_tree,
    "demo": cmd_demo,
}


def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    cmd = sys.argv[1]
    fn = COMMANDS.get(cmd)
    if not fn:
        print(f"unknown command: {cmd}"); return
    fn(sys.argv[2:])


if __name__ == "__main__":
    main()
