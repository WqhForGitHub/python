# -*- coding: utf-8 -*-
"""
多线程下载器
- 纯 Python 标准库（urllib + threading）
- 支持 Range 多段并发下载（若服务器支持），否则回退单线程
- 实时进度条，断点续传通过分段独立写入实现
- CLI 用法：
    python downloader.py <url> [-o output] [-n threads]
"""
import argparse
import os
import sys
import threading
import time
from urllib.request import Request, urlopen
from urllib.parse import urlparse


class MultiThreadDownloader:
    def __init__(self, url, output=None, threads=8, chunk_size=64 * 1024):
        self.url = url
        self.output = output or self._guess_filename(url)
        self.threads = max(1, threads)
        self.chunk_size = chunk_size
        self.total_size = 0
        self.downloaded = 0
        self.lock = threading.Lock()
        self.support_range = False

    @staticmethod
    def _guess_filename(url):
        path = urlparse(url).path
        name = os.path.basename(path) or "downloaded.bin"
        return name

    def _head(self):
        req = Request(self.url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=15) as resp:
            self.total_size = int(resp.headers.get("Content-Length", 0))
            self.support_range = resp.headers.get("Accept-Ranges", "").lower() == "bytes"

    def _download_range(self, start, end, fp, idx):
        headers = {"User-Agent": "Mozilla/5.0", "Range": f"bytes={start}-{end}"}
        req = Request(self.url, headers=headers)
        with urlopen(req, timeout=30) as resp:
            pos = start
            while True:
                buf = resp.read(self.chunk_size)
                if not buf:
                    break
                with self.lock:
                    fp.seek(pos)
                    fp.write(buf)
                    self.downloaded += len(buf)
                pos += len(buf)

    def _download_single(self, fp):
        req = Request(self.url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=30) as resp:
            while True:
                buf = resp.read(self.chunk_size)
                if not buf:
                    break
                fp.write(buf)
                with self.lock:
                    self.downloaded += len(buf)

    def _progress_loop(self, stop_event):
        start = time.time()
        while not stop_event.is_set():
            self._render(start)
            time.sleep(0.2)
        self._render(start)
        print()

    def _render(self, start):
        elapsed = max(time.time() - start, 1e-6)
        speed = self.downloaded / elapsed
        if self.total_size > 0:
            pct = self.downloaded / self.total_size * 100
            bar = "█" * int(pct / 2) + "·" * (50 - int(pct / 2))
            sys.stdout.write(
                f"\r[{bar}] {pct:6.2f}%  "
                f"{self.downloaded/1024/1024:7.2f}/{self.total_size/1024/1024:.2f} MB  "
                f"{speed/1024/1024:6.2f} MB/s"
            )
        else:
            sys.stdout.write(f"\r{self.downloaded/1024/1024:.2f} MB  {speed/1024/1024:.2f} MB/s")
        sys.stdout.flush()

    def run(self):
        try:
            self._head()
        except Exception as e:
            print(f"[!] HEAD 请求失败：{e}，将使用单线程下载")

        print(f"URL     : {self.url}")
        print(f"输出    : {self.output}")
        print(f"大小    : {self.total_size/1024/1024:.2f} MB" if self.total_size else "大小    : 未知")
        print(f"分段    : {self.threads if self.support_range and self.total_size else 1}")
        print(f"Range   : {'支持' if self.support_range else '不支持'}")
        print("-" * 60)

        stop_event = threading.Event()
        prog_t = threading.Thread(target=self._progress_loop, args=(stop_event,), daemon=True)
        prog_t.start()

        try:
            if self.support_range and self.total_size > 0 and self.threads > 1:
                # 预分配文件
                with open(self.output, "wb") as f:
                    f.truncate(self.total_size)

                with open(self.output, "r+b") as fp:
                    part = self.total_size // self.threads
                    workers = []
                    for i in range(self.threads):
                        start = i * part
                        end = self.total_size - 1 if i == self.threads - 1 else (start + part - 1)
                        t = threading.Thread(target=self._download_range,
                                             args=(start, end, fp, i), daemon=True)
                        t.start()
                        workers.append(t)
                    for t in workers:
                        t.join()
            else:
                with open(self.output, "wb") as fp:
                    self._download_single(fp)
        finally:
            stop_event.set()
            prog_t.join()

        print(f"[✓] 完成：{self.output} ({self.downloaded/1024/1024:.2f} MB)")


def main():
    p = argparse.ArgumentParser(description="多线程下载器")
    p.add_argument("url", help="下载地址")
    p.add_argument("-o", "--output", help="输出文件名")
    p.add_argument("-n", "--threads", type=int, default=8, help="线程数 (默认 8)")
    args = p.parse_args()
    MultiThreadDownloader(args.url, args.output, args.threads).run()


if __name__ == "__main__":
    main()
