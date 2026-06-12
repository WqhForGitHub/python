"""
文件重命名工具
支持批量重命名、序号命名、前缀/后缀添加、
查找替换、大小写转换等操作，提供预览功能。
"""

import os
import re
import sys
from pathlib import Path

# ── 重命名操作 ────────────────────────────────────────────


def add_prefix(name: str, prefix: str) -> str:
    """添加前缀。"""
    return prefix + name


def add_suffix(name: str, suffix: str) -> str:
    """添加后缀（在扩展名之前）。"""
    p = Path(name)
    return p.stem + suffix + p.suffix


def replace_text(name: str, old: str, new: str) -> str:
    """替换文件名中的文本。"""
    return name.replace(old, new)


def replace_regex(name: str, pattern: str, repl: str) -> str:
    """正则替换文件名。"""
    try:
        return re.sub(pattern, repl, name)
    except re.error:
        print(f"  正则表达式错误: {pattern}")
        return name


def to_lowercase(name: str) -> str:
    """文件名转小写。"""
    p = Path(name)
    return p.stem.lower() + p.suffix.lower()


def to_uppercase(name: str) -> str:
    """文件名转大写。"""
    p = Path(name)
    return p.stem.upper() + p.suffix.upper()


def sequential_number(name: str, num: int, width: int = 3) -> str:
    """序号命名（替换原文件名）。"""
    p = Path(name)
    return str(num).zfill(width) + p.suffix


def insert_number(name: str, num: int, width: int = 3) -> str:
    """在文件名前插入序号。"""
    p = Path(name)
    return str(num).zfill(width) + "_" + name


def remove_pattern(name: str, pattern: str) -> str:
    """删除匹配的文本。"""
    return re.sub(pattern, "", name)


# ── 批量操作 ──────────────────────────────────────────────


def get_files(directory: str, pattern: str = "*") -> list[Path]:
    """获取目录中匹配的文件。"""
    p = Path(directory)
    if not p.is_dir():
        print(f"  错误：'{directory}' 不是有效目录")
        return []
    return sorted(p.glob(pattern))


def preview_rename(files: list[Path], new_names: list[str]) -> None:
    """预览重命名结果。"""
    print("\n  ═══ 重命名预览 ═══")
    for old, new in zip(files, new_names):
        if old.name == new:
            print(f"  {old.name} → （无变化）")
        else:
            print(f"  {old.name} → {new}")
    print()


def execute_rename(files: list[Path], new_names: list[str]) -> tuple[int, int]:
    """执行重命名，返回 (成功数, 失败数)。"""
    success, fail = 0, 0
    for old, new in zip(files, new_names):
        if old.name == new:
            continue
        new_path = old.parent / new
        try:
            old.rename(new_path)
            success += 1
        except Exception as e:
            print(f"  重命名失败: {old.name} → {new} ({e})")
            fail += 1
    return success, fail


# ── 操作菜单 ──────────────────────────────────────────────


def apply_operation(files: list[Path], op_name: str) -> list[str] | None:
    """对文件列表应用指定操作，返回新文件名列表。"""
    new_names = []
    for i, f in enumerate(files, 1):
        name = f.name
        if op_name == "1":
            prefix = input("  前缀: ").strip()
            if not prefix:
                return None
            new_names.append(add_prefix(name, prefix))
        elif op_name == "2":
            suffix = input("  后缀: ").strip()
            if not suffix:
                return None
            new_names.append(add_suffix(name, suffix))
        elif op_name == "3":
            if i == 1:
                global _old, _new
                _old = input("  查找: ").strip()
                _new = input("  替换为: ").strip()
            new_names.append(replace_text(name, _old, _new))
        elif op_name == "4":
            if i == 1:
                global _pat, _rep
                _pat = input("  正则表达式: ").strip()
                _rep = input("  替换为: ").strip()
            new_names.append(replace_regex(name, _pat, _rep))
        elif op_name == "5":
            new_names.append(to_lowercase(name))
        elif op_name == "6":
            new_names.append(to_uppercase(name))
        elif op_name == "7":
            width = 3
            if i == 1:
                raw = input("  序号位数（默认3）: ").strip()
                if raw:
                    try:
                        width = int(raw)
                    except ValueError:
                        width = 3
            new_names.append(sequential_number(name, i, width))
        elif op_name == "8":
            width = 3
            if i == 1:
                raw = input("  序号位数（默认3）: ").strip()
                if raw:
                    try:
                        width = int(raw)
                    except ValueError:
                        width = 3
            new_names.append(insert_number(name, i, width))
        elif op_name == "9":
            if i == 1:
                global _rm_pat
                _rm_pat = input("  要删除的模式（正则）: ").strip()
            new_names.append(remove_pattern(name, _rm_pat))
        else:
            return None
        # 之后的文件不再需要询问参数
        if i == 1 and op_name in ("1", "2"):
            # 前缀/后缀只需要问一次，但上面的循环每次都问
            pass

    return new_names


# 为了解决重复询问的问题，重写 apply_operation


def apply_operation_v2(files: list[Path], op_name: str) -> list[str] | None:
    """对文件列表应用指定操作（只询问一次参数）。"""
    # 先获取操作参数
    if op_name == "1":
        prefix = input("  前缀: ").strip()
        if not prefix:
            return None
        return [add_prefix(f.name, prefix) for f in files]
    elif op_name == "2":
        suffix = input("  后缀（加在扩展名前）: ").strip()
        if not suffix:
            return None
        return [add_suffix(f.name, suffix) for f in files]
    elif op_name == "3":
        old = input("  查找: ").strip()
        new = input("  替换为: ").strip()
        return [replace_text(f.name, old, new) for f in files]
    elif op_name == "4":
        pat = input("  正则表达式: ").strip()
        rep = input("  替换为: ").strip()
        return [replace_regex(f.name, pat, rep) for f in files]
    elif op_name == "5":
        return [to_lowercase(f.name) for f in files]
    elif op_name == "6":
        return [to_uppercase(f.name) for f in files]
    elif op_name == "7":
        raw = input("  序号位数（默认3）: ").strip()
        width = int(raw) if raw else 3
        return [sequential_number(f.name, i, width) for i, f in enumerate(files, 1)]
    elif op_name == "8":
        raw = input("  序号位数（默认3）: ").strip()
        width = int(raw) if raw else 3
        return [insert_number(f.name, i, width) for i, f in enumerate(files, 1)]
    elif op_name == "9":
        pat = input("  要删除的文本: ").strip()
        return [f.name.replace(pat, "") for f in files]
    return None


# ── 主菜单 ────────────────────────────────────────────────


def print_menu() -> None:
    print("=" * 45)
    print("  文件重命名工具")
    print("=" * 45)
    print("  1. 添加前缀")
    print("  2. 添加后缀")
    print("  3. 查找替换")
    print("  4. 正则替换")
    print("  5. 转小写")
    print("  6. 转大写")
    print("  7. 序号命名（替换文件名）")
    print("  8. 插入序号（保留文件名）")
    print("  9. 删除指定文本")
    print("  q. 退出")
    print("-" * 45)


def main() -> None:
    while True:
        print_menu()
        choice = input("  请选择操作: ").strip()

        if choice == "q":
            print("  再见！")
            break

        if choice not in ("1", "2", "3", "4", "5", "6", "7", "8", "9"):
            print("  无效选择")
            continue

        directory = input("  目录路径: ").strip()
        if not directory:
            continue

        filter_pat = input("  文件过滤（如 *.txt，默认 *）: ").strip() or "*"

        files = [f for f in get_files(directory, filter_pat) if f.is_file()]
        if not files:
            print("  未找到匹配的文件")
            continue

        print(f"  找到 {len(files)} 个文件")
        new_names = apply_operation_v2(files, choice)
        if new_names is None:
            continue

        preview_rename(files, new_names)

        confirm = input("  确认执行重命名？(y/N): ").strip().lower()
        if confirm == "y":
            success, fail = execute_rename(files, new_names)
            print(f"  完成：成功 {success} 个，失败 {fail} 个")
        else:
            print("  已取消")


if __name__ == "__main__":
    main()
