"""
ZIP 压缩 demo
功能：
    - 压缩文件 / 整个目录到 zip
    - 支持过滤规则（通配符 include/exclude）
    - 列出 zip 内容（含大小、压缩率、修改时间）
    - 解压 zip 到目标目录（防止 zip-slip 路径穿越）
    - 压缩级别可选（store / deflate）
    - 实现：基于标准库 zipfile，纯 Python，无第三方
"""

import os
import fnmatch
import shutil
import zipfile
from datetime import datetime


# -------- 压缩 --------

def zip_dir(src_dir: str, zip_path: str,
            include: list = None, exclude: list = None,
            compression: str = "deflate") -> dict:
    """压缩目录"""
    if not os.path.isdir(src_dir):
        raise FileNotFoundError(src_dir)

    comp = (zipfile.ZIP_DEFLATED if compression == "deflate"
            else zipfile.ZIP_STORED)

    files_added = 0
    bytes_in = 0
    with zipfile.ZipFile(zip_path, "w", compression=comp) as zf:
        for cur, dirs, files in os.walk(src_dir):
            for fn in files:
                full = os.path.join(cur, fn)
                rel = os.path.relpath(full, src_dir).replace(os.sep, "/")
                if not _match_filter(rel, include, exclude):
                    continue
                zf.write(full, arcname=rel)
                files_added += 1
                bytes_in += os.path.getsize(full)
    return {
        "zip": zip_path,
        "files": files_added,
        "uncompressed": bytes_in,
        "compressed": os.path.getsize(zip_path),
        "ratio": (1 - os.path.getsize(zip_path) / bytes_in) * 100
                 if bytes_in else 0,
    }


def zip_files(file_paths: list, zip_path: str,
              compression: str = "deflate") -> dict:
    comp = (zipfile.ZIP_DEFLATED if compression == "deflate"
            else zipfile.ZIP_STORED)
    bytes_in = 0
    with zipfile.ZipFile(zip_path, "w", compression=comp) as zf:
        for p in file_paths:
            zf.write(p, arcname=os.path.basename(p))
            bytes_in += os.path.getsize(p)
    return {
        "zip": zip_path,
        "files": len(file_paths),
        "uncompressed": bytes_in,
        "compressed": os.path.getsize(zip_path),
    }


def _match_filter(name: str, include: list, exclude: list) -> bool:
    if exclude and any(fnmatch.fnmatch(name, p) for p in exclude):
        return False
    if include and not any(fnmatch.fnmatch(name, p) for p in include):
        return False
    return True


# -------- 列出 --------

def list_zip(zip_path: str) -> list:
    out = []
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            ratio = (1 - info.compress_size / info.file_size) * 100 \
                if info.file_size else 0
            out.append({
                "name": info.filename,
                "size": info.file_size,
                "compressed": info.compress_size,
                "ratio": ratio,
                "mtime": datetime(*info.date_time).strftime("%Y-%m-%d %H:%M"),
                "is_dir": info.is_dir(),
            })
    return out


# -------- 解压 --------

def unzip(zip_path: str, dest_dir: str,
          overwrite: bool = False) -> dict:
    """解压 zip，防止 zip-slip"""
    os.makedirs(dest_dir, exist_ok=True)
    abs_dest = os.path.abspath(dest_dir)
    extracted = 0
    skipped = 0
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            target = os.path.abspath(os.path.join(dest_dir, info.filename))
            if not target.startswith(abs_dest + os.sep) and target != abs_dest:
                # 阻止路径穿越
                skipped += 1
                continue
            if os.path.exists(target) and not overwrite:
                skipped += 1
                continue
            if info.is_dir():
                os.makedirs(target, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with zf.open(info) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                extracted += 1
    return {"extracted": extracted, "skipped": skipped,
            "dest": dest_dir}


# ==================== Demo ====================

def fmt_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f}{unit}" if unit != "B" else f"{n}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


if __name__ == "__main__":
    print("=" * 60)
    print("  ZIP 压缩工具 Demo")
    print("=" * 60)

    base = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(base, "data")
    out_zip = os.path.join(base, "data.zip")
    extract_dir = os.path.join(base, "unzipped")

    # 准备测试数据
    for d in (src_dir, extract_dir):
        if os.path.exists(d):
            shutil.rmtree(d)
        os.makedirs(d)
    if os.path.exists(out_zip):
        os.remove(out_zip)

    # 创建若干测试文件
    files = {
        "readme.txt": "Hello ZIP demo\n" * 50,
        "a.log": "log entry " * 200,
        "b.log": "another log " * 200,
        "src/main.py": "print('hello')\n" * 30,
        "src/utils.py": "def f(): pass\n" * 40,
        "img/a.bin": "B" * 4096,
        "img/b.bin": "C" * 4096,
        ".gitignore": "*.log\n__pycache__/\n",
    }
    for rel, content in files.items():
        full = os.path.join(src_dir, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)

    # 1. 压缩整个目录
    print("\n--- 1. 压缩整个目录 ---")
    res = zip_dir(src_dir, out_zip)
    print(f"  files: {res['files']}")
    print(f"  原始: {fmt_size(res['uncompressed'])}  "
          f"压缩后: {fmt_size(res['compressed'])}  "
          f"压缩率: {res['ratio']:.1f}%")

    # 2. 列出 zip
    print("\n--- 2. zip 内容 ---")
    print(f"  {'文件':<25}{'原始':>10}{'压缩':>10}{'压缩率':>9}  {'修改时间'}")
    print("  " + "-" * 70)
    for it in list_zip(out_zip):
        print(f"  {it['name']:<25}{fmt_size(it['size']):>10}"
              f"{fmt_size(it['compressed']):>10}{it['ratio']:>8.1f}%  {it['mtime']}")

    # 3. 仅打包 *.py + readme，并排除 src/utils.py
    os.remove(out_zip)
    print("\n--- 3. 过滤打包：include=['*.py','readme.*']  exclude=['*/utils.py'] ---")
    res = zip_dir(src_dir, out_zip,
                  include=["*.py", "readme.*"],
                  exclude=["*/utils.py"])
    print(f"  files: {res['files']}")
    for it in list_zip(out_zip):
        print(f"    - {it['name']}")

    # 4. 解压
    print("\n--- 4. 解压到 unzipped/ ---")
    res = unzip(out_zip, extract_dir)
    print(f"  解压: {res['extracted']} 个文件, 跳过: {res['skipped']}")

    print("\n  解压后目录树:")
    for cur, dirs, fs in os.walk(extract_dir):
        depth = cur[len(extract_dir):].count(os.sep)
        print("    " + "  " * depth + os.path.basename(cur) + "/")
        for fn in fs:
            print("    " + "  " * (depth + 1) + fn)

    # 5. 单独压缩几个文件
    print("\n--- 5. 仅压缩单个文件 ---")
    only_zip = os.path.join(base, "only.zip")
    res = zip_files(
        [os.path.join(src_dir, "readme.txt"),
         os.path.join(src_dir, "a.log")],
        only_zip, compression="store",
    )
    print(f"  files: {res['files']}, size: {fmt_size(res['compressed'])}"
          " (store 模式不压缩)")

    # 清理
    for p in (out_zip, only_zip):
        if os.path.exists(p):
            os.remove(p)
    shutil.rmtree(src_dir, ignore_errors=True)
    shutil.rmtree(extract_dir, ignore_errors=True)

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
