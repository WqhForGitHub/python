"""
自动备份脚本
功能：将指定源目录备份为 zip / tar.gz 归档，支持增量备份（基于文件修改时间）、
      文件过滤（包含/排除模式）、版本保留（按数量/天数）、备份摘要、还原等
"""

import os
import re
import shutil
import zipfile
import tarfile
import json
import hashlib
from datetime import datetime, timedelta


class AutoBackup:
    """自动备份"""

    def __init__(
        self,
        source_dir: str,
        backup_dir: str,
        archive_format: str = "zip",  # zip / tar.gz / dir
        include: list = None,
        exclude: list = None,
        keep_count: int = 5,
        keep_days: int = None,
    ):
        self.source_dir = os.path.abspath(source_dir)
        self.backup_dir = os.path.abspath(backup_dir)
        self.archive_format = archive_format
        self.include = include or []
        self.exclude = exclude or []
        self.keep_count = keep_count
        self.keep_days = keep_days

        os.makedirs(self.backup_dir, exist_ok=True)

        self.manifest_file = os.path.join(self.backup_dir, ".backup_manifest.json")
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> dict:
        """加载清单文件"""
        if os.path.exists(self.manifest_file):
            try:
                with open(self.manifest_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (IOError, json.JSONDecodeError):
                pass
        return {"backups": [], "last_full": None, "file_hashes": {}}

    def _save_manifest(self):
        """保存清单文件"""
        with open(self.manifest_file, "w", encoding="utf-8") as f:
            json.dump(self.manifest, f, ensure_ascii=False, indent=2)

    def _match_pattern(self, filename: str, pattern: str) -> bool:
        """简单 glob 匹配"""
        regex = (
            pattern.replace(".", r"\.").replace("*", ".*").replace("?", ".")
        )
        return bool(re.fullmatch(regex, filename, re.IGNORECASE))

    def _should_include(self, rel_path: str) -> bool:
        """是否应包含该文件"""
        name = os.path.basename(rel_path)

        # 排除优先
        for pat in self.exclude:
            if self._match_pattern(name, pat) or self._match_pattern(rel_path, pat):
                return False

        # 包含模式
        if self.include:
            return any(
                self._match_pattern(name, p) or self._match_pattern(rel_path, p)
                for p in self.include
            )
        return True

    def _file_hash(self, filepath: str, block_size: int = 65536) -> str:
        """计算文件 MD5"""
        h = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for block in iter(lambda: f.read(block_size), b""):
                    h.update(block)
        except (IOError, OSError):
            return ""
        return h.hexdigest()

    def _collect_files(self) -> list:
        """收集要备份的文件"""
        files = []
        for root, dirs, filenames in os.walk(self.source_dir):
            # 排除隐藏目录
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for fname in filenames:
                full = os.path.join(root, fname)
                rel = os.path.relpath(full, self.source_dir)
                if self._should_include(rel):
                    files.append((full, rel))
        return files

    def backup(self, incremental: bool = False, label: str = "") -> dict:
        """执行备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_type = "incremental" if incremental else "full"
        prefix = label + "_" if label else ""
        base_name = f"{prefix}backup_{backup_type}_{timestamp}"

        print(f"\n>>> 开始 {backup_type} 备份: {base_name}")
        print(f"    源: {self.source_dir}")

        all_files = self._collect_files()
        print(f"    发现文件: {len(all_files)}")

        # 增量备份：仅含已变更文件
        files_to_backup = []
        new_hashes = {}
        last_hashes = self.manifest.get("file_hashes", {}) if incremental else {}

        for full, rel in all_files:
            h = self._file_hash(full)
            new_hashes[rel] = h
            if not incremental or last_hashes.get(rel) != h:
                files_to_backup.append((full, rel))

        if incremental:
            print(f"    已变更文件: {len(files_to_backup)}")

        if not files_to_backup:
            print("    无文件变更，跳过备份")
            return {"skipped": True, "reason": "no_changes"}

        # 创建归档
        if self.archive_format == "zip":
            archive_path = os.path.join(self.backup_dir, base_name + ".zip")
            self._create_zip(archive_path, files_to_backup)
        elif self.archive_format == "tar.gz":
            archive_path = os.path.join(self.backup_dir, base_name + ".tar.gz")
            self._create_tar(archive_path, files_to_backup)
        elif self.archive_format == "dir":
            archive_path = os.path.join(self.backup_dir, base_name)
            self._create_dir(archive_path, files_to_backup)
        else:
            raise ValueError(f"不支持的格式: {self.archive_format}")

        # 计算大小
        if os.path.isfile(archive_path):
            size = os.path.getsize(archive_path)
        else:
            size = sum(
                os.path.getsize(os.path.join(r, f))
                for r, _, fs in os.walk(archive_path)
                for f in fs
            )

        # 更新清单
        info = {
            "name": base_name,
            "path": archive_path,
            "type": backup_type,
            "format": self.archive_format,
            "timestamp": timestamp,
            "created_at": datetime.now().isoformat(),
            "file_count": len(files_to_backup),
            "size_bytes": size,
            "label": label,
        }
        self.manifest["backups"].append(info)
        self.manifest["file_hashes"] = new_hashes
        if not incremental:
            self.manifest["last_full"] = base_name
        self._save_manifest()

        print(f"    完成: {archive_path}")
        print(f"    文件数: {len(files_to_backup)}  大小: {size:,} 字节")

        # 清理旧备份
        self._cleanup_old_backups()

        return info

    def _create_zip(self, archive_path: str, files: list):
        """创建 zip 归档"""
        with zipfile.ZipFile(
            archive_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6
        ) as zf:
            for full, rel in files:
                try:
                    zf.write(full, rel)
                except (IOError, OSError) as e:
                    print(f"    [警告] 跳过 {rel}: {e}")

    def _create_tar(self, archive_path: str, files: list):
        """创建 tar.gz 归档"""
        with tarfile.open(archive_path, "w:gz") as tf:
            for full, rel in files:
                try:
                    tf.add(full, arcname=rel)
                except (IOError, OSError) as e:
                    print(f"    [警告] 跳过 {rel}: {e}")

    def _create_dir(self, archive_path: str, files: list):
        """复制到目录"""
        os.makedirs(archive_path, exist_ok=True)
        for full, rel in files:
            dest = os.path.join(archive_path, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            try:
                shutil.copy2(full, dest)
            except (IOError, OSError) as e:
                print(f"    [警告] 跳过 {rel}: {e}")

    def _cleanup_old_backups(self):
        """清理旧备份"""
        backups = sorted(
            self.manifest["backups"], key=lambda b: b["timestamp"], reverse=True
        )

        to_delete = []

        # 按数量保留
        if self.keep_count and len(backups) > self.keep_count:
            to_delete.extend(backups[self.keep_count :])

        # 按天数保留
        if self.keep_days:
            cutoff = datetime.now() - timedelta(days=self.keep_days)
            for b in backups:
                try:
                    t = datetime.strptime(b["timestamp"], "%Y%m%d_%H%M%S")
                    if t < cutoff and b not in to_delete:
                        to_delete.append(b)
                except ValueError:
                    pass

        # 执行删除
        for b in to_delete:
            path = b["path"]
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    os.remove(path)
            self.manifest["backups"].remove(b)
            print(f"    [清理] 删除旧备份: {b['name']}")

        if to_delete:
            self._save_manifest()

    def list_backups(self) -> list:
        """列出所有备份"""
        return sorted(
            self.manifest["backups"], key=lambda b: b["timestamp"], reverse=True
        )

    def restore(self, backup_name: str, target_dir: str) -> bool:
        """还原备份"""
        backup = next(
            (b for b in self.manifest["backups"] if b["name"] == backup_name), None
        )
        if not backup:
            print(f"未找到备份: {backup_name}")
            return False

        path = backup["path"]
        if not os.path.exists(path):
            print(f"备份文件丢失: {path}")
            return False

        os.makedirs(target_dir, exist_ok=True)
        fmt = backup["format"]

        try:
            if fmt == "zip":
                with zipfile.ZipFile(path, "r") as zf:
                    zf.extractall(target_dir)
            elif fmt == "tar.gz":
                with tarfile.open(path, "r:gz") as tf:
                    tf.extractall(target_dir)
            elif fmt == "dir":
                for root, dirs, files in os.walk(path):
                    rel_root = os.path.relpath(root, path)
                    dest_root = (
                        target_dir
                        if rel_root == "."
                        else os.path.join(target_dir, rel_root)
                    )
                    os.makedirs(dest_root, exist_ok=True)
                    for f in files:
                        shutil.copy2(os.path.join(root, f), os.path.join(dest_root, f))
            print(f"还原完成: {path} -> {target_dir}")
            return True
        except Exception as e:
            print(f"还原失败: {e}")
            return False

    def print_status(self):
        """打印状态"""
        backups = self.list_backups()
        print(f"\n--- 备份列表 ({len(backups)} 个) ---")
        print(f"{'名称':<45s} {'类型':<12s} {'文件数':>6s} {'大小':>12s}")
        print("-" * 85)
        for b in backups:
            size_str = f"{b['size_bytes']:,}"
            print(
                f"{b['name']:<45s} {b['type']:<12s} "
                f"{b['file_count']:>6d} {size_str:>12s}"
            )


# ==================== 演示 ====================


def create_demo_source(demo_dir: str) -> str:
    """创建演示源目录"""
    src = os.path.join(demo_dir, "source")
    os.makedirs(os.path.join(src, "docs"), exist_ok=True)
    os.makedirs(os.path.join(src, "code"), exist_ok=True)
    os.makedirs(os.path.join(src, ".cache"), exist_ok=True)

    files = {
        "README.md": "# 项目\n这是源目录。",
        "docs/intro.md": "介绍文档",
        "docs/guide.md": "使用指南",
        "code/main.py": 'print("hello")',
        "code/utils.py": "def add(a, b): return a + b",
        "code/temp.pyc": "binary cache",  # 应被排除
        "config.json": '{"version": 1}',
        ".cache/data.bin": "cache",  # 隐藏目录会被排除
    }
    for rel, content in files.items():
        full = os.path.join(src, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)

    return src


def cleanup_demo(demo_dir: str):
    for sub in ["source", "backups", "restored"]:
        p = os.path.join(demo_dir, sub)
        if os.path.exists(p):
            shutil.rmtree(p, ignore_errors=True)


if __name__ == "__main__":
    print("=" * 60)
    print("  自动备份脚本 Demo")
    print("=" * 60)

    demo_dir = os.path.dirname(os.path.abspath(__file__))
    cleanup_demo(demo_dir)

    src = create_demo_source(demo_dir)
    backup_dir = os.path.join(demo_dir, "backups")

    try:
        # 1. 全量备份 (zip)
        backup = AutoBackup(
            source_dir=src,
            backup_dir=backup_dir,
            archive_format="zip",
            exclude=["*.pyc", "*.tmp"],
            keep_count=3,
        )
        backup.backup(incremental=False, label="daily")

        # 2. 修改文件后增量备份
        print("\n[模拟] 修改 README.md 并新增 newfile.txt")
        with open(os.path.join(src, "README.md"), "a", encoding="utf-8") as f:
            f.write("\n\n## 更新\n版本 2.0")
        with open(os.path.join(src, "newfile.txt"), "w", encoding="utf-8") as f:
            f.write("这是新文件")

        backup.backup(incremental=True, label="daily")

        # 3. 无变更增量备份
        print("\n[场景] 无任何变更")
        backup.backup(incremental=True, label="daily")

        # 4. tar.gz 全量备份
        backup2 = AutoBackup(
            source_dir=src,
            backup_dir=backup_dir,
            archive_format="tar.gz",
            keep_count=3,
        )
        backup2.backup(incremental=False, label="weekly")

        # 5. 列出所有备份
        backup.print_status()

        # 6. 还原最近一次全量备份
        backups = backup.list_backups()
        full_backup = next((b for b in backups if b["type"] == "full"), None)
        if full_backup:
            print(f"\n>>> 还原备份: {full_backup['name']}")
            restore_dir = os.path.join(demo_dir, "restored")
            backup.restore(full_backup["name"], restore_dir)
            # 列出还原内容
            print("还原后内容:")
            for root, _, files in os.walk(restore_dir):
                for f in files:
                    rel = os.path.relpath(os.path.join(root, f), restore_dir)
                    print(f"  {rel}")

        # 7. 演示版本保留（创建多个备份触发清理）
        print("\n>>> 演示保留策略 (keep_count=3)")
        for i in range(4):
            with open(os.path.join(src, "README.md"), "a", encoding="utf-8") as f:
                f.write(f"\nrev {i}")
            backup.backup(incremental=False, label=f"test{i}")
        backup.print_status()

    finally:
        cleanup_demo(demo_dir)

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
