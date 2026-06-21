"""
文件分类整理器
功能：
    - 按扩展名将杂乱目录的文件自动分类到 图片/文档/视频/音频/压缩包/代码 等子目录
    - 支持按修改时间分类（年/月）
    - 支持按文件大小分类
    - 同名文件自动重命名（追加 _1、_2 ...）
    - 支持 dry-run 预览
    - 可撤销（undo）：依据移动日志将文件还原回原位置
"""

import os
import re
import json
import shutil
from datetime import datetime


# 扩展名分类规则
DEFAULT_CATEGORIES = {
    "图片": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".tiff", ".ico"],
    "文档": [
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".txt", ".md", ".rtf", ".odt", ".epub",
    ],
    "视频": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
    "音频": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"],
    "压缩包": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"],
    "代码": [
        ".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".cs",
        ".go", ".rs", ".rb", ".php", ".html", ".css", ".sh", ".sql", ".json", ".xml", ".yaml", ".yml",
    ],
    "可执行": [".exe", ".msi", ".bat", ".cmd", ".apk", ".dmg"],
    "数据": [".csv", ".tsv", ".db", ".sqlite", ".log"],
}


class FileOrganizer:
    """文件分类整理器"""

    def __init__(self, target_dir: str, categories: dict = None):
        self.target_dir = os.path.abspath(target_dir)
        self.categories = categories or DEFAULT_CATEGORIES
        # 反向索引: ext -> category
        self._ext_map = {}
        for cat, exts in self.categories.items():
            for ext in exts:
                self._ext_map[ext.lower()] = cat

    # -------- 主分类方法 --------
    def organize(self, mode="extension", dry_run=False) -> dict:
        """整理文件

        mode:
            'extension' - 按扩展名分类
            'date'      - 按修改时间(年/月)分类
            'size'      - 按文件大小(小/中/大)分类
        """
        if not os.path.isdir(self.target_dir):
            raise FileNotFoundError(self.target_dir)

        moves = []
        for fname in os.listdir(self.target_dir):
            src = os.path.join(self.target_dir, fname)
            if not os.path.isfile(src):
                continue
            if fname.startswith("."):
                continue

            sub = self._categorize(src, mode)
            target_dir = os.path.join(self.target_dir, sub)
            target_path = self._unique_path(os.path.join(target_dir, fname))

            moves.append({"from": src, "to": target_path, "category": sub})

            if not dry_run:
                os.makedirs(target_dir, exist_ok=True)
                shutil.move(src, target_path)

        # 记录移动日志（用于 undo）
        log_path = os.path.join(self.target_dir, ".organize_log.json")
        if moves and not dry_run:
            self._append_log(log_path, moves)

        # 统计
        stats = {}
        for m in moves:
            stats[m["category"]] = stats.get(m["category"], 0) + 1

        return {
            "dry_run": dry_run,
            "mode": mode,
            "total": len(moves),
            "stats": stats,
            "moves": moves,
        }

    def _categorize(self, filepath: str, mode: str) -> str:
        if mode == "extension":
            ext = os.path.splitext(filepath)[1].lower()
            return self._ext_map.get(ext, "其他")
        elif mode == "date":
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            return os.path.join(str(mtime.year), f"{mtime.month:02d}")
        elif mode == "size":
            size = os.path.getsize(filepath)
            if size < 1024 * 1024:        # < 1MB
                return "小文件"
            elif size < 100 * 1024 * 1024:  # < 100MB
                return "中文件"
            else:
                return "大文件"
        else:
            raise ValueError(f"未知模式: {mode}")

    def _unique_path(self, path: str) -> str:
        """避免覆盖：若目标存在则在文件名后添加 _1, _2"""
        if not os.path.exists(path):
            return path
        base, ext = os.path.splitext(path)
        i = 1
        while True:
            candidate = f"{base}_{i}{ext}"
            if not os.path.exists(candidate):
                return candidate
            i += 1

    def _append_log(self, log_path: str, moves: list):
        records = []
        if os.path.isfile(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    records = json.load(f)
            except (json.JSONDecodeError, OSError):
                records = []
        records.append(
            {
                "time": datetime.now().isoformat(timespec="seconds"),
                "moves": moves,
            }
        )
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

    # -------- 撤销 --------
    def undo(self) -> dict:
        """撤销最近一次整理"""
        log_path = os.path.join(self.target_dir, ".organize_log.json")
        if not os.path.isfile(log_path):
            return {"undone": 0, "msg": "无操作日志"}

        with open(log_path, "r", encoding="utf-8") as f:
            records = json.load(f)
        if not records:
            return {"undone": 0, "msg": "无可撤销的操作"}

        last = records.pop()
        undone = 0
        for m in reversed(last["moves"]):
            if os.path.isfile(m["to"]):
                try:
                    os.makedirs(os.path.dirname(m["from"]), exist_ok=True)
                    shutil.move(m["to"], m["from"])
                    undone += 1
                except (OSError, shutil.Error):
                    pass

        # 清理空子目录
        self._remove_empty_dirs(self.target_dir)

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

        return {"undone": undone, "msg": "已撤销最近一次整理"}

    def _remove_empty_dirs(self, root: str):
        for cur, dirs, files in os.walk(root, topdown=False):
            if cur == root:
                continue
            try:
                if not os.listdir(cur):
                    os.rmdir(cur)
            except OSError:
                pass


# ==================== Demo ====================


def make_file(path: str, size: int = 64, mtime=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"x" * size)
    if mtime:
        ts = mtime.timestamp()
        os.utime(path, (ts, ts))


def show_tree(root: str, label: str):
    print(f"  [{label}] {root}")
    if not os.path.isdir(root):
        return
    for cur, dirs, files in os.walk(root):
        depth = cur[len(root) :].count(os.sep)
        indent = "    " + "  " * depth
        name = os.path.basename(cur) if depth else "."
        print(f"{indent}{name}/")
        for fn in files:
            if fn == ".organize_log.json":
                continue
            print(f"{indent}  {fn}")


if __name__ == "__main__":
    print("=" * 60)
    print("  文件分类整理器 Demo")
    print("=" * 60)

    base = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(base, "messy")

    if os.path.exists(target):
        shutil.rmtree(target)
    os.makedirs(target)

    # 准备杂乱文件
    samples = [
        ("photo1.jpg", 100),
        ("photo2.PNG", 200),
        ("report.pdf", 500),
        ("readme.md", 80),
        ("song.mp3", 300),
        ("movie.mp4", 1500),
        ("archive.zip", 700),
        ("script.py", 120),
        ("style.css", 90),
        ("data.csv", 150),
        ("setup.exe", 2000),
        ("unknown.xyz", 60),
        ("notes.txt", 40),
    ]
    for fn, size in samples:
        make_file(os.path.join(target, fn), size=size)

    print("\n--- 整理前 ---")
    show_tree(target, "目录")

    organizer = FileOrganizer(target)

    # 1. dry-run 预览
    print("\n--- 1. Dry-run 预览（按扩展名） ---")
    preview = organizer.organize(mode="extension", dry_run=True)
    for m in preview["moves"]:
        print(f"  {os.path.basename(m['from']):<20} -> {m['category']}/")
    print(f"  共 {preview['total']} 个文件")

    # 2. 实际整理
    print("\n--- 2. 执行整理（按扩展名） ---")
    result = organizer.organize(mode="extension")
    print(f"  共移动 {result['total']} 个文件")
    for cat, cnt in sorted(result["stats"].items()):
        print(f"    {cat}: {cnt}")
    show_tree(target, "整理后")

    # 3. 撤销
    print("\n--- 3. 撤销整理 ---")
    undo_result = organizer.undo()
    print(f"  {undo_result['msg']}, 还原 {undo_result['undone']} 个文件")
    show_tree(target, "撤销后")

    # 4. 按日期整理
    print("\n--- 4. 按修改时间(年/月)整理 ---")
    # 给部分文件设置不同 mtime
    make_file(
        os.path.join(target, "old_photo.jpg"),
        size=120,
        mtime=datetime(2023, 5, 10, 9, 0, 0),
    )
    make_file(
        os.path.join(target, "old_doc.txt"),
        size=80,
        mtime=datetime(2024, 8, 20, 14, 30, 0),
    )
    res = organizer.organize(mode="date")
    print(f"  共移动 {res['total']} 个文件")
    show_tree(target, "按日期")

    # 撤销
    organizer.undo()

    # 5. 按大小整理
    print("\n--- 5. 按文件大小整理 ---")
    res = organizer.organize(mode="size")
    print(f"  共移动 {res['total']} 个文件")
    for cat, cnt in res["stats"].items():
        print(f"    {cat}: {cnt}")
    show_tree(target, "按大小")

    # 清理
    shutil.rmtree(target, ignore_errors=True)

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
