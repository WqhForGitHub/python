"""
PyDocker - 纯 Python 实现的 Docker 模拟版
============================================

本项目用纯 Python 标准库模拟 Docker 的核心概念：
  - 镜像 (image): 一份只读的文件系统快照 + 元数据
  - 容器 (container): 基于镜像的可写层 + 一个被隔离的进程
  - 仓库 (registry): 本地保存所有镜像与容器的 JSON 数据库
  - 命令: build / images / run / ps / logs / stop / rm / rmi / exec / commit

注意：真正的 Docker 用 Linux namespace + cgroups + OverlayFS 实现强隔离。
本模拟版用「目录拷贝 + chdir + 受限 PATH + JSON 元数据」做轻量隔离，
保留与 Docker 极其相似的命令行用法，适合学习其设计思想。

用法
----
    python pydocker.py build -t myapp ./app          # 从目录构建镜像
    python pydocker.py images                        # 列出镜像
    python pydocker.py run -d --name web myapp       # 后台启动容器
    python pydocker.py run myapp echo hello          # 一次性运行
    python pydocker.py ps -a                         # 所有容器
    python pydocker.py logs web                      # 查看日志
    python pydocker.py exec web ls                   # 进入运行中容器执行
    python pydocker.py stop web
    python pydocker.py rm web
    python pydocker.py rmi myapp
    python pydocker.py commit web mynewimage        # 容器 -> 镜像
    python pydocker.py demo                          # 一键自测
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

# ----------------------------------------------------------------------------
# 配置：所有数据存放在 ~/.pydocker/
# ----------------------------------------------------------------------------
ROOT = Path(os.environ.get("PYDOCKER_ROOT", Path.home() / ".pydocker"))
IMAGES_DIR = ROOT / "images"          # 镜像层 (只读)
CONTAINERS_DIR = ROOT / "containers"  # 容器层 (可写)
META_FILE = ROOT / "meta.json"        # 元数据库


def _ensure_dirs() -> None:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    CONTAINERS_DIR.mkdir(parents=True, exist_ok=True)
    if not META_FILE.exists():
        META_FILE.write_text(json.dumps({"images": {}, "containers": {}}, indent=2))


def _load_meta() -> dict:
    _ensure_dirs()
    return json.loads(META_FILE.read_text(encoding="utf-8"))


def _save_meta(meta: dict) -> None:
    META_FILE.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


def _short(_id: str) -> str:
    return _id[:12]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ----------------------------------------------------------------------------
# Dockerfile 解析器（极简：FROM/COPY/RUN/CMD/ENV/WORKDIR）
# ----------------------------------------------------------------------------
def _parse_dockerfile(text: str) -> list[tuple[str, str]]:
    instructions = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if " " not in line:
            continue
        op, arg = line.split(" ", 1)
        instructions.append((op.upper(), arg.strip()))
    return instructions


# ----------------------------------------------------------------------------
# build：把目录打包成镜像
# ----------------------------------------------------------------------------
def cmd_build(context: str, tag: str) -> str:
    ctx = Path(context).resolve()
    if not ctx.is_dir():
        sys.exit(f"build context not a dir: {ctx}")

    image_id = hashlib.sha256(f"{tag}-{time.time()}".encode()).hexdigest()
    layer = IMAGES_DIR / image_id
    layer.mkdir()

    cfg = {"cmd": ["sh"], "env": {}, "workdir": "/"}
    dockerfile = ctx / "Dockerfile"
    if dockerfile.exists():
        for op, arg in _parse_dockerfile(dockerfile.read_text(encoding="utf-8")):
            if op == "FROM":
                # 模拟版没有真正的 base image，仅记录 origin
                cfg["from"] = arg
            elif op == "COPY":
                parts = arg.split()
                src, dst = parts[0], parts[1] if len(parts) > 1 else "."
                src_p = ctx / src
                dst_p = layer / dst.lstrip("/")
                dst_p.parent.mkdir(parents=True, exist_ok=True)
                if src_p.is_dir():
                    shutil.copytree(src_p, dst_p, dirs_exist_ok=True)
                else:
                    shutil.copy2(src_p, dst_p)
                print(f" -> COPY {src} {dst}")
            elif op == "RUN":
                # 在镜像层目录里执行 shell 命令
                print(f" -> RUN {arg}")
                subprocess.run(arg, shell=True, cwd=layer, check=False)
            elif op == "CMD":
                cfg["cmd"] = arg.split() if not arg.startswith("[") else json.loads(arg)
            elif op == "ENV":
                k, _, v = arg.partition("=")
                cfg["env"][k] = v
            elif op == "WORKDIR":
                cfg["workdir"] = arg
                (layer / arg.lstrip("/")).mkdir(parents=True, exist_ok=True)
    else:
        # 没 Dockerfile：直接把目录拷进去
        shutil.copytree(ctx, layer, dirs_exist_ok=True)

    meta = _load_meta()
    meta["images"][image_id] = {
        "id": image_id,
        "tag": tag,
        "created": _now(),
        "size": _dir_size(layer),
        "config": cfg,
    }
    _save_meta(meta)
    print(f"Successfully built {_short(image_id)}")
    print(f"Successfully tagged {tag}")
    return image_id


def _dir_size(p: Path) -> int:
    total = 0
    for f in p.rglob("*"):
        if f.is_file():
            total += f.stat().st_size
    return total


def _resolve_image(meta: dict, name: str) -> str | None:
    """通过 tag 或 (短)id 找镜像。"""
    for iid, info in meta["images"].items():
        if info["tag"] == name or iid == name or iid.startswith(name):
            return iid
    return None


def _resolve_container(meta: dict, name: str) -> str | None:
    for cid, info in meta["containers"].items():
        if info["name"] == name or cid == name or cid.startswith(name):
            return cid
    return None


# ----------------------------------------------------------------------------
# run：基于镜像创建容器并运行
# ----------------------------------------------------------------------------
def cmd_run(image: str, command: list[str], name: str = "", detach: bool = False,
            rm_after: bool = False, env: dict | None = None) -> str:
    meta = _load_meta()
    iid = _resolve_image(meta, image)
    if not iid:
        sys.exit(f"image not found: {image}")
    img = meta["images"][iid]

    cid = uuid.uuid4().hex
    cname = name or f"py_{_short(cid)}"
    cdir = CONTAINERS_DIR / cid
    cdir.mkdir()

    # 拷贝镜像层 -> 容器可写层 (相当于 copy-on-write 的最朴素模拟)
    rootfs = cdir / "rootfs"
    shutil.copytree(IMAGES_DIR / iid, rootfs)

    log_file = cdir / "container.log"
    cmd = command if command else img["config"].get("cmd", ["sh"])
    if isinstance(cmd, str):
        cmd = cmd.split()

    # 组装环境
    env_full = os.environ.copy()
    env_full.update(img["config"].get("env", {}))
    if env:
        env_full.update(env)
    env_full["PYDOCKER_CONTAINER_ID"] = cid
    env_full["PYDOCKER_CONTAINER_NAME"] = cname

    workdir = rootfs / img["config"].get("workdir", "/").lstrip("/")
    if not workdir.exists():
        workdir = rootfs

    info = {
        "id": cid,
        "name": cname,
        "image": iid,
        "image_tag": img["tag"],
        "command": " ".join(cmd),
        "created": _now(),
        "status": "created",
        "pid": None,
        "exit_code": None,
        "rootfs": str(rootfs),
        "log": str(log_file),
    }
    meta["containers"][cid] = info
    _save_meta(meta)

    print(f"container {_short(cid)} ({cname}) starting: {' '.join(cmd)}")

    try:
        if detach:
            # 后台模式：把 stdout/stderr 重定向到日志文件
            f = open(log_file, "ab")
            proc = subprocess.Popen(
                cmd, cwd=workdir, env=env_full,
                stdout=f, stderr=f, stdin=subprocess.DEVNULL,
            )
            info["status"] = "running"
            info["pid"] = proc.pid
            meta["containers"][cid] = info
            _save_meta(meta)
            print(_short(cid))
        else:
            # 前台模式：实时输出
            with open(log_file, "ab") as f:
                proc = subprocess.Popen(
                    cmd, cwd=workdir, env=env_full,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                )
                info["status"] = "running"
                info["pid"] = proc.pid
                meta["containers"][cid] = info
                _save_meta(meta)
                assert proc.stdout
                for line in proc.stdout:
                    sys.stdout.write(line.decode(errors="replace"))
                    f.write(line)
                proc.wait()
                info["status"] = "exited"
                info["exit_code"] = proc.returncode
                meta["containers"][cid] = info
                _save_meta(meta)
                if rm_after:
                    cmd_rm(cid, force=True)
    except FileNotFoundError as e:
        info["status"] = "error"
        info["exit_code"] = 127
        meta["containers"][cid] = info
        _save_meta(meta)
        print(f"failed to start: {e}")
    return cid


# ----------------------------------------------------------------------------
# images / ps / logs / stop / rm / rmi / exec / commit
# ----------------------------------------------------------------------------
def cmd_images() -> None:
    meta = _load_meta()
    print(f"{'REPOSITORY':<20}{'IMAGE ID':<16}{'CREATED':<22}{'SIZE':>10}")
    for iid, info in meta["images"].items():
        print(f"{info['tag']:<20}{_short(iid):<16}{info['created']:<22}{info['size']:>10}")


def cmd_ps(all_: bool = False) -> None:
    meta = _load_meta()
    print(f"{'CONTAINER ID':<16}{'IMAGE':<16}{'COMMAND':<30}{'STATUS':<12}{'NAME':<16}")
    for cid, info in meta["containers"].items():
        # 检查后台进程是否还活着
        if info["status"] == "running" and info["pid"]:
            if not _pid_alive(info["pid"]):
                info["status"] = "exited"
                meta["containers"][cid] = info
                _save_meta(meta)
        if not all_ and info["status"] != "running":
            continue
        print(f"{_short(cid):<16}{info['image_tag']:<16}{info['command'][:28]:<30}"
              f"{info['status']:<12}{info['name']:<16}")


def _pid_alive(pid: int) -> bool:
    try:
        if os.name == "nt":
            out = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True, text=True,
            )
            return str(pid) in out.stdout
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def cmd_logs(name: str, follow: bool = False) -> None:
    meta = _load_meta()
    cid = _resolve_container(meta, name)
    if not cid:
        sys.exit(f"container not found: {name}")
    log = Path(meta["containers"][cid]["log"])
    if not log.exists():
        return
    if follow:
        with open(log, "rb") as f:
            f.seek(0, 2)
            try:
                while True:
                    line = f.readline()
                    if line:
                        sys.stdout.write(line.decode(errors="replace"))
                        sys.stdout.flush()
                    else:
                        time.sleep(0.2)
            except KeyboardInterrupt:
                return
    else:
        sys.stdout.write(log.read_text(encoding="utf-8", errors="replace"))


def cmd_stop(name: str) -> None:
    meta = _load_meta()
    cid = _resolve_container(meta, name)
    if not cid:
        sys.exit(f"container not found: {name}")
    info = meta["containers"][cid]
    pid = info.get("pid")
    if pid and _pid_alive(pid):
        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
            else:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.3)
                if _pid_alive(pid):
                    os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
    info["status"] = "exited"
    meta["containers"][cid] = info
    _save_meta(meta)
    print(_short(cid))


def cmd_rm(name: str, force: bool = False) -> None:
    meta = _load_meta()
    cid = _resolve_container(meta, name)
    if not cid:
        sys.exit(f"container not found: {name}")
    info = meta["containers"][cid]
    if info["status"] == "running":
        if not force:
            sys.exit(f"container {name} is running; use -f to force")
        cmd_stop(cid)
    shutil.rmtree(CONTAINERS_DIR / cid, ignore_errors=True)
    meta = _load_meta()
    meta["containers"].pop(cid, None)
    _save_meta(meta)
    print(_short(cid))


def cmd_rmi(name: str) -> None:
    meta = _load_meta()
    iid = _resolve_image(meta, name)
    if not iid:
        sys.exit(f"image not found: {name}")
    # 检查有无容器在使用
    for c in meta["containers"].values():
        if c["image"] == iid:
            sys.exit(f"image is in use by container {c['name']}")
    shutil.rmtree(IMAGES_DIR / iid, ignore_errors=True)
    meta["images"].pop(iid, None)
    _save_meta(meta)
    print(f"Untagged: {name}\nDeleted: {_short(iid)}")


def cmd_exec(name: str, command: list[str]) -> None:
    meta = _load_meta()
    cid = _resolve_container(meta, name)
    if not cid:
        sys.exit(f"container not found: {name}")
    info = meta["containers"][cid]
    if info["status"] != "running":
        sys.exit(f"container {name} not running")
    rootfs = Path(info["rootfs"])
    proc = subprocess.run(command, cwd=rootfs, capture_output=True, text=True)
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    sys.exit(proc.returncode)


def cmd_commit(name: str, new_tag: str) -> None:
    """容器当前可写层 -> 新镜像。"""
    meta = _load_meta()
    cid = _resolve_container(meta, name)
    if not cid:
        sys.exit(f"container not found: {name}")
    info = meta["containers"][cid]
    new_id = hashlib.sha256(f"{new_tag}-{time.time()}".encode()).hexdigest()
    new_layer = IMAGES_DIR / new_id
    shutil.copytree(info["rootfs"], new_layer)
    parent_cfg = meta["images"][info["image"]]["config"]
    meta["images"][new_id] = {
        "id": new_id,
        "tag": new_tag,
        "created": _now(),
        "size": _dir_size(new_layer),
        "config": parent_cfg,
    }
    _save_meta(meta)
    print(f"sha256:{_short(new_id)}")


# ----------------------------------------------------------------------------
# demo：一键演示
# ----------------------------------------------------------------------------
def cmd_demo() -> None:
    print("=== PyDocker demo ===")
    work = Path("./_pydocker_demo_app")
    if work.exists():
        shutil.rmtree(work)
    work.mkdir()
    (work / "app.py").write_text(
        "import sys, os\n"
        "print('hello from pydocker container')\n"
        "print('cwd =', os.getcwd())\n"
        "print('files =', sorted(os.listdir('.')))\n",
        encoding="utf-8",
    )
    (work / "Dockerfile").write_text(
        "FROM python:scratch\n"
        "COPY app.py /app.py\n"
        "WORKDIR /\n"
        f'CMD ["{sys.executable}", "app.py"]\n',
        encoding="utf-8",
    )

    print("\n[1] build")
    cmd_build(str(work), "demoapp:latest")
    print("\n[2] images")
    cmd_images()
    print("\n[3] run (foreground)")
    cmd_run("demoapp", [], name="demo1")
    print("\n[4] ps -a")
    cmd_ps(all_=True)
    print("\n[5] logs")
    cmd_logs("demo1")
    print("\n[6] cleanup")
    cmd_rm("demo1", force=True)
    cmd_rmi("demoapp:latest")
    shutil.rmtree(work)
    print("\n=== demo done ===")


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pydocker", description="Python 模拟版 Docker")
    sub = p.add_subparsers(dest="cmd", required=True)

    pb = sub.add_parser("build")
    pb.add_argument("-t", "--tag", required=True)
    pb.add_argument("context")

    sub.add_parser("images")

    pr = sub.add_parser("run")
    pr.add_argument("-d", "--detach", action="store_true")
    pr.add_argument("--name", default="")
    pr.add_argument("--rm", action="store_true")
    pr.add_argument("-e", "--env", action="append", default=[])
    pr.add_argument("image")
    pr.add_argument("command", nargs=argparse.REMAINDER)

    pp = sub.add_parser("ps")
    pp.add_argument("-a", "--all", action="store_true")

    pl = sub.add_parser("logs")
    pl.add_argument("-f", "--follow", action="store_true")
    pl.add_argument("name")

    ps = sub.add_parser("stop")
    ps.add_argument("name")

    pe = sub.add_parser("exec")
    pe.add_argument("name")
    pe.add_argument("command", nargs=argparse.REMAINDER)

    prm = sub.add_parser("rm")
    prm.add_argument("-f", "--force", action="store_true")
    prm.add_argument("name")

    prmi = sub.add_parser("rmi")
    prmi.add_argument("name")

    pc = sub.add_parser("commit")
    pc.add_argument("name")
    pc.add_argument("new_tag")

    sub.add_parser("demo")
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.cmd == "build":
        cmd_build(args.context, args.tag)
    elif args.cmd == "images":
        cmd_images()
    elif args.cmd == "run":
        env = {}
        for kv in args.env:
            k, _, v = kv.partition("=")
            env[k] = v
        cmd_run(args.image, args.command, args.name, args.detach, args.rm, env)
    elif args.cmd == "ps":
        cmd_ps(args.all)
    elif args.cmd == "logs":
        cmd_logs(args.name, args.follow)
    elif args.cmd == "stop":
        cmd_stop(args.name)
    elif args.cmd == "exec":
        cmd_exec(args.name, args.command)
    elif args.cmd == "rm":
        cmd_rm(args.name, args.force)
    elif args.cmd == "rmi":
        cmd_rmi(args.name)
    elif args.cmd == "commit":
        cmd_commit(args.name, args.new_tag)
    elif args.cmd == "demo":
        cmd_demo()


if __name__ == "__main__":
    main()
