"""
文件大小统计器
扫描指定目录，统计文件大小、类型分布，
支持排序、过滤、树形展示等功能。
"""

import os
import sys
from pathlib import Path

# ── 大小格式化 ────────────────────────────────────────────


def format_size(size: int) -> str:
    """将字节数格式化为人类可读的大小。"""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def format_count(count: int) -> str:
    """格式化数量。"""
    return f"{count:,}"


# ── 扫描逻辑 ──────────────────────────────────────────────


def scan_directory(directory: str) -> list[dict]:
    """扫描目录，返回文件信息列表。"""
    files = []
    root = Path(directory)
    if not root.is_dir():
        print(f"  错误：'{directory}' 不是有效目录")
        return []

    for path in root.rglob("*"):
        if path.is_file():
            try:
                stat = path.stat()
                files.append(
                    {
                        "path": str(path),
                        "name": path.name,
                        "ext": path.suffix.lower() if path.suffix else "(无扩展名)",
                        "size": stat.st_size,
                        "parent": str(path.parent),
                    }
                )
            except (PermissionError, OSError):
                pass

    return files


def group_by_extension(files: list[dict]) -> dict[str, list[dict]]:
    """按扩展名分组。"""
    groups: dict[str, list[dict]] = {}
    for f in files:
        ext = f["ext"]
        if ext not in groups:
            groups[ext] = []
        groups[ext].append(f)
    return groups


# ── 统计展示 ──────────────────────────────────────────────


def show_summary(files: list[dict]) -> None:
    """展示总体统计。"""
    if not files:
        print("  未找到文件")
        return

    total_size = sum(f["size"] for f in files)
    avg_size = total_size / len(files)
    max_file = max(files, key=lambda f: f["size"])
    min_file = min(files, key=lambda f: f["size"])

    print(f"\n  ═══ 文件大小统计 ═══")
    print(f"  文件总数　：{format_count(len(files))}")
    print(f"  总大小　　：{format_size(total_size)}")
    print(f"  平均大小　：{format_size(avg_size)}")
    print(f"  最大文件　：{max_file['name']} ({format_size(max_file['size'])})")
    print(f"  最小文件　：{min_file['name']} ({format_size(min_file['size'])})")
    print()


def show_by_extension(files: list[dict]) -> None:
    """按扩展名展示统计。"""
    groups = group_by_extension(files)
    # 按总大小降序排列
    sorted_groups = sorted(
        groups.items(), key=lambda x: sum(f["size"] for f in x[1]), reverse=True
    )

    total_size = sum(f["size"] for f in files)

    print(f"\n  ═══ 按类型统计 ═══")
    print(f"  {'类型':<12s} {'数量':>8s} {'大小':>12s} {'占比':>8s}")
    print(f"  {'─' * 12} {'─' * 8} {'─' * 12} {'─' * 8}")

    for ext, file_list in sorted_groups:
        ext_size = sum(f["size"] for f in file_list)
        pct = (ext_size / total_size * 100) if total_size > 0 else 0
        bar = "█" * int(pct / 5)
        print(
            f"  {ext:<12s} {len(file_list):>8s} {format_size(ext_size):>12s} {pct:>6.1f}% {bar}"
        )

    print()


def show_top_n(files: list[dict], n: int = 10) -> None:
    """展示最大的 N 个文件。"""
    sorted_files = sorted(files, key=lambda f: f["size"], reverse=True)[:n]

    print(f"\n  ═══ 最大的 {n} 个文件 ═══")
    for i, f in enumerate(sorted_files, 1):
        print(f"  {i:>2d}. {format_size(f['size']):>10s}  {f['name']}")
    print()


def show_size_distribution(files: list[dict]) -> None:
    """展示文件大小分布。"""
    ranges = [
        ("0 - 1KB", 0, 1024),
        ("1KB - 100KB", 1024, 102400),
        ("100KB - 1MB", 102400, 1048576),
        ("1MB - 10MB", 1048576, 10485760),
        ("10MB - 100MB", 10485760, 104857600),
        ("100MB - 1GB", 104857600, 1073741824),
        ("> 1GB", 1073741824, float("inf")),
    ]

    print(f"\n  ═══ 大小分布 ═══")
    for label, low, high in ranges:
        count = sum(1 for f in files if low <= f["size"] < high)
        if count > 0:
            bar = "█" * min(count, 40)
            print(f"  {label:<14s} {count:>6d} {bar}")
    print()


# ── 主菜单 ────────────────────────────────────────────────


def print_menu() -> None:
    print("=" * 45)
    print("  文件大小统计器")
    print("=" * 45)
    print("  1. 扫描目录并查看总体统计")
    print("  2. 按文件类型统计")
    print("  3. 查看最大文件 TOP 10")
    print("  4. 查看大小分布")
    print("  5. 完整统计报告")
    print("  q. 退出")
    print("-" * 45)


def main() -> None:
    cached_files: list[dict] = []

    while True:
        print_menu()
        choice = input("  请选择: ").strip()

        if choice == "q":
            print("  再见！")
            break

        if choice in ("1", "2", "3", "4", "5"):
            directory = input("  目录路径: ").strip()
            if not directory:
                continue

            print("  扫描中...")
            files = scan_directory(directory)
            if not files:
                continue
            cached_files = files
            print(f"  扫描完成，共 {len(files)} 个文件")

            if choice == "1":
                show_summary(files)
            elif choice == "2":
                show_by_extension(files)
            elif choice == "3":
                raw = input("  显示前 N 个（默认10）: ").strip()
                n = int(raw) if raw else 10
                show_top_n(files, n)
            elif choice == "4":
                show_size_distribution(files)
            elif choice == "5":
                show_summary(files)
                show_by_extension(files)
                show_top_n(files)
                show_size_distribution(files)

        else:
            print("  无效选择，请重新输入")


if __name__ == "__main__":
    main()
