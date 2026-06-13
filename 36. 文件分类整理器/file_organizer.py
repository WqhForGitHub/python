"""
文件分类整理器
功能：根据文件类型/扩展名/日期/大小将杂乱目录中的文件自动分类到子目录中，
      支持自定义规则、预览(dry-run)模式、撤销操作、统计报告等
"""

import os
import shutil
import json
import time
from datetime import datetime
from collections import defaultdict


class FileOrganizer:
    """文件分类整理器"""

    # 默认分类规则：类别名 -> 扩展名列表
    DEFAULT_RULES = {
        "图片": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico"],
        "视频": [".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm"],
        "音频": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"],
        "文档": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
                 ".txt", ".md", ".rtf", ".odt"],
        "压缩包": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
        "代码": [".py", ".js", ".java", ".c", ".cpp", ".h", ".html", ".css",
                 ".go", ".rs", ".ts", ".php", ".rb"],
        "数据": [".json", ".xml", ".csv", ".yaml", ".yml", ".sql", ".db"],
        "可执行": [".exe", ".msi", ".dmg", ".deb", ".rpm", ".apk"],
        "字体": [".ttf", ".otf", ".woff", ".woff2"],
    }

    def __init__(self, rules: dict = None, other_folder: str = "其他"):
        self.rules = rules or dict(self.DEFAULT_RULES)
        self.other_folder = other_folder
        # 反向映射：扩展名 -> 类别
        self._ext_map = {}
        self._build_ext_map()
        # 操作历史，用于撤销
        self.history = []

    def _build_ext_map(self):
        """构建扩展名 -> 类别 映射"""
        self._ext_map = {}
        for category, exts in self.rules.items():
            for ext in exts:
                self._ext_map[ext.lower()] = category

    def add_rule(self, category: str, extensions: list):
        """添加或更新分类规则"""
        if category in self.rules:
            self.rules[category].extend(extensions)
        else:
            self.rules[category] = list(extensions)
        self._build_ext_map()

    def get_category(self, filename: str) -> str:
        """根据文件名获取分类"""
        ext = os.path.splitext(filename)[1].lower()
        return self._ext_map.get(ext, self.other_folder)

    # ==================== 核心整理 ====================

    def organize_by_type(self, src_dir: str, dst_dir: str = None,
                        dry_run: bool = False, recursive: bool = False) -> dict:
        """按类型整理文件
        src_dir: 源目录
        dst_dir: 目标目录（默认与源目录相同）
        dry_run: 仅预览不实际移动
        recursive: 是否递归处理子目录
        """
        if not os.path.isdir(src_dir):
            raise ValueError(f"源目录不存在: {src_dir}")

        dst_dir = dst_dir or src_dir
        stats = defaultdict(int)
        moves = []

        files = self._collect_files(src_dir, recursive)

        for filepath in files:
            filename = os.path.basename(filepath)
            category = self.get_category(filename)
            target_dir = os.path.join(dst_dir, category)
            target_path = os.path.join(target_dir, filename)

            # 处理重名
            target_path = self._resolve_conflict(target_path)

            moves.append((filepath, target_path, category))
            stats[category] += 1

        # 执行移动
        if not dry_run:
            for src, dst, _ in moves:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.move(src, dst)
                self.history.append({"src": src, "dst": dst,
                                     "time": datetime.now().isoformat()})

        return {
            "total": len(moves),
            "stats": dict(stats),
            "moves": moves,
            "dry_run": dry_run,
        }

    def organize_by_date(self, src_dir: str, dst_dir: str = None,
                        granularity: str = "month", dry_run: bool = False) -> dict:
        """按修改日期整理
        granularity: year/month/day
        """
        if not os.path.isdir(src_dir):
            raise ValueError(f"源目录不存在: {src_dir}")

        dst_dir = dst_dir or src_dir
        stats = defaultdict(int)
        moves = []

        files = self._collect_files(src_dir, recursive=False)

        fmt_map = {
            "year": "%Y",
            "month": "%Y-%m",
            "day": "%Y-%m-%d",
        }
        fmt = fmt_map.get(granularity, "%Y-%m")

        for filepath in files:
            filename = os.path.basename(filepath)
            mtime = os.path.getmtime(filepath)
            folder = datetime.fromtimestamp(mtime).strftime(fmt)
            target_dir = os.path.join(dst_dir, folder)
            target_path = self._resolve_conflict(os.path.join(target_dir, filename))
            moves.append((filepath, target_path, folder))
            stats[folder] += 1

        if not dry_run:
            for src, dst, _ in moves:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.move(src, dst)
                self.history.append({"src": src, "dst": dst,
                                     "time": datetime.now().isoformat()})

        return {
            "total": len(moves),
            "stats": dict(stats),
            "moves": moves,
            "dry_run": dry_run,
        }

    def organize_by_size(self, src_dir: str, dst_dir: str = None,
                        dry_run: bool = False) -> dict:
        """按文件大小整理"""
        if not os.path.isdir(src_dir):
            raise ValueError(f"源目录不存在: {src_dir}")

        dst_dir = dst_dir or src_dir
        stats = defaultdict(int)
        moves = []

        files = self._collect_files(src_dir, recursive=False)

        for filepath in files:
            filename = os.path.basename(filepath)
            size = os.path.getsize(filepath)
            category = self._size_category(size)
            target_dir = os.path.join(dst_dir, category)
            target_path = self._resolve_conflict(os.path.join(target_dir, filename))
            moves.append((filepath, target_path, category))
            stats[category] += 1

        if not dry_run:
            for src, dst, _ in moves:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.move(src, dst)
                self.history.append({"src": src, "dst": dst,
                                     "time": datetime.now().isoformat()})

        return {
            "total": len(moves),
            "stats": dict(stats),
            "moves": moves,
            "dry_run": dry_run,
        }

    @staticmethod
    def _size_category(size: int) -> str:
        """大小类别"""
        if size < 10 * 1024:
            return "微小(<10KB)"
        elif size < 1024 * 1024:
            return "小(<1MB)"
        elif size < 10 * 1024 * 1024:
            return "中(<10MB)"
        elif size < 100 * 1024 * 1024:
            return "大(<100MB)"
        else:
            return "超大(>=100MB)"

    def _collect_files(self, src_dir: str, recursive: bool) -> list:
        """收集要处理的文件"""
        files = []
        if recursive:
            for root, dirs, filenames in os.walk(src_dir):
                # 排除我们创建的分类目录
                dirs[:] = [d for d in dirs
                          if d not in self.rules and d != self.other_folder]
                for fname in filenames:
                    if not fname.startswith("."):
                        files.append(os.path.join(root, fname))
        else:
            for fname in os.listdir(src_dir):
                fp = os.path.join(src_dir, fname)
                if os.path.isfile(fp) and not fname.startswith("."):
                    files.append(fp)
        return files

    @staticmethod
    def _resolve_conflict(path: str) -> str:
        """解决文件重名冲突，自动加序号"""
        if not os.path.exists(path):
            return path
        base, ext = os.path.splitext(path)
        counter = 1
        while True:
            new_path = f"{base}_{counter}{ext}"
            if not os.path.exists(new_path):
                return new_path
            counter += 1

    # ==================== 撤销 / 报告 ====================

    def undo(self) -> int:
        """撤销最后一批操作"""
        count = 0
        while self.history:
            record = self.history.pop()
            src = record["dst"]  # 当前位置
            dst = record["src"]  # 原始位置
            if os.path.exists(src):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.move(src, dst)
                count += 1
        return count

    def save_history(self, filepath: str):
        """保存操作历史"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def load_history(self, filepath: str):
        """加载操作历史"""
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                self.history = json.load(f)

    @staticmethod
    def print_report(result: dict, title: str = "整理报告"):
        """打印整理报告"""
        print(f"\n--- {title} ---")
        mode = "[预览]" if result.get("dry_run") else "[已执行]"
        print(f"模式: {mode}")
        print(f"处理文件总数: {result['total']}")
        print("分类统计:")
        for cat, n in sorted(result["stats"].items(), key=lambda x: -x[1]):
            print(f"  {cat:12s}: {n} 个")
        if result["total"] <= 20:
            print("详细移动:")
            for src, dst, cat in result["moves"]:
                print(f"  [{cat}] {os.path.basename(src)} -> "
                      f"{os.path.relpath(dst, os.path.dirname(src))}")


# ==================== 演示 ====================

def create_demo_files(demo_dir: str):
    """创建演示用的杂乱文件"""
    files = [
        ("照片1.jpg", b"FAKE_JPG"),
        ("照片2.png", b"FAKE_PNG"),
        ("假期视频.mp4", b"FAKE_MP4" * 1000),
        ("音乐.mp3", b"FAKE_MP3" * 500),
        ("简历.pdf", b"FAKE_PDF"),
        ("报告.docx", b"FAKE_DOCX"),
        ("数据表.xlsx", b"FAKE_XLSX"),
        ("笔记.txt", "这是一个文本文件".encode("utf-8")),
        ("说明.md", b"# Hello"),
        ("源代码.py", b"print('hi')"),
        ("脚本.js", b"console.log(1)"),
        ("数据.json", b'{"a":1}'),
        ("配置.yaml", b"key: value"),
        ("归档.zip", b"FAKE_ZIP" * 200),
        ("安装包.exe", b"FAKE_EXE" * 1500),
        ("奇怪文件.xyz", b"unknown"),
        ("图标.ico", b"FAKE_ICO"),
        ("字体.ttf", b"FAKE_TTF"),
    ]
    os.makedirs(demo_dir, exist_ok=True)
    for name, content in files:
        path = os.path.join(demo_dir, name)
        with open(path, "wb") as f:
            f.write(content)
        # 设置不同的修改时间用于按日期演示
        mtime = time.time() - (hash(name) % 90) * 86400
        os.utime(path, (mtime, mtime))


def cleanup_demo(demo_dir: str):
    """清理演示目录"""
    if os.path.exists(demo_dir):
        shutil.rmtree(demo_dir)


if __name__ == "__main__":
    print("=" * 60)
    print("  文件分类整理器 Demo")
    print("=" * 60)

    base_dir = os.path.dirname(__file__)
    demo_dir = os.path.join(base_dir, "demo_messy")

    organizer = FileOrganizer()

    # 1. 创建演示文件
    print("\n--- 1. 创建演示文件 ---")
    cleanup_demo(demo_dir)
    create_demo_files(demo_dir)
    print(f"在 {demo_dir} 中创建了 {len(os.listdir(demo_dir))} 个杂乱文件")

    # 2. 预览整理（dry-run）
    print("\n--- 2. 按类型整理（预览模式） ---")
    result = organizer.organize_by_type(demo_dir, dry_run=True)
    FileOrganizer.print_report(result, "类型整理预览")

    # 3. 实际执行按类型整理
    print("\n--- 3. 实际执行整理 ---")
    result = organizer.organize_by_type(demo_dir, dry_run=False)
    FileOrganizer.print_report(result, "类型整理结果")
    print("\n整理后目录结构:")
    for entry in sorted(os.listdir(demo_dir)):
        ep = os.path.join(demo_dir, entry)
        if os.path.isdir(ep):
            sub = os.listdir(ep)
            print(f"  [{entry}/] ({len(sub)} 个文件)")
            for f in sub:
                print(f"      - {f}")

    # 4. 撤销
    print("\n--- 4. 撤销刚才的整理 ---")
    n = organizer.undo()
    print(f"已撤销 {n} 个文件的移动")
    print(f"当前根目录文件数: "
          f"{len([x for x in os.listdir(demo_dir) if os.path.isfile(os.path.join(demo_dir, x))])}")

    # 5. 按大小整理
    print("\n--- 5. 按文件大小整理（预览） ---")
    result = organizer.organize_by_size(demo_dir, dry_run=True)
    FileOrganizer.print_report(result, "大小整理预览")

    # 6. 按日期整理（预览）
    print("\n--- 6. 按修改日期整理（按月，预览） ---")
    result = organizer.organize_by_date(demo_dir, granularity="month", dry_run=True)
    FileOrganizer.print_report(result, "日期整理预览")

    # 7. 自定义规则
    print("\n--- 7. 添加自定义规则：未知扩展名归到'神秘文件' ---")
    organizer.other_folder = "神秘文件"
    organizer.add_rule("Web前端", [".html", ".css"])
    result = organizer.organize_by_type(demo_dir, dry_run=True)
    FileOrganizer.print_report(result, "自定义规则预览")

    # 8. 单文件类别查询
    print("\n--- 8. 查询单文件类别 ---")
    test_files = ["abc.jpg", "song.flac", "doc.pdf", "weird.xyz", "code.py"]
    for f in test_files:
        print(f"  {f:15s} -> {organizer.get_category(f)}")

    # 清理
    cleanup_demo(demo_dir)

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
