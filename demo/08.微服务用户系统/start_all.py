"""一键启动全部三个服务（演示用，仅 Windows/Unix 通用）。

运行：
    python start_all.py

会以子进程方式拉起 api-gateway / auth-service / user-service，
Ctrl+C 统一退出。
"""
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent

services = [
    ("api-gateway", "api-gateway/main.py", 8000),
    ("auth-service", "auth-service/main.py", 8001),
    ("user-service", "user-service/main.py", 8002),
]

procs: list[subprocess.Popen] = []


def main() -> None:
    try:
        for name, rel, port in services:
            print(f"[start] {name} on :{port}")
            procs.append(
                subprocess.Popen(
                    [
                        sys.executable, "-m", "uvicorn",
                        f"main:app", "--port", str(port), "--host", "0.0.0.0",
                    ],
                    cwd=str(ROOT / Path(rel).parent),
                )
            )
            time.sleep(1.5)  # 等网关先就绪
        print("\n全部服务已启动：")
        print("  gateway : http://127.0.0.1:8000/docs")
        print("  auth    : http://127.0.0.1:8001/docs")
        print("  user    : http://127.0.0.1:8002/docs")
        print("\nCtrl+C 退出全部服务\n")
        for p in procs:
            p.wait()
    except KeyboardInterrupt:
        print("\n[stop] 收到退出信号，关闭全部服务...")
    finally:
        for p in procs:
            if p.poll() is None:
                try:
                    p.send_signal(signal.SIGTERM)
                except Exception:  # noqa: BLE001
                    pass
        for p in procs:
            try:
                p.wait(timeout=5)
            except Exception:  # noqa: BLE001
                p.kill()


if __name__ == "__main__":
    main()
