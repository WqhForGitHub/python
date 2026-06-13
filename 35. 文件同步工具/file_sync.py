"""
文件同步工具
功能：将源目录同步到目标目录（类 rsync 单向同步），支持：
      - 增量同步（基于大小+修改时间，可选 hash 校验）
      - 干跑模式（dry-run，仅预览不修改）
      - 双向比对（diff）
      - 删除目标多余文件（mirror 模式）
      - 文件过滤（include/exclude）
      - 同步结果报告
"""

import os
import shutil
import hashlib
import re
from datetime import datetime


class FileSync:
    """文件同步工具"""

    def __init__(
        self,
        source: str,
        target: str,
        include: list = None,
        exclude: list = None,
        delete: bool = False,
        use_hash: bool = False,
        dry_run: bool = False,
    ):
        self.source = os.path.abspath(source)
        self.target = os.path.abspath(target)
        self.include = include or []
        self.exclude = exclude or []
        self.delete = delete
        self.use_hash = use_hash
        self.dry_run = dry_run

        # 同步操作
        self.actions = {
            "add": [],  # 新增文件 (target 没有)
            "update": [],  # 更新文件 (内容不同)
            "skip": [],  # 跳过 (相同)
            "delete": [],  # 删除 (target 多余)
            "error": [],  # 错误
        }

    def _match_pattern(self, name: str, pattern: str) -> bool:
        regex = pattern.replace(".", r"\.").replace("*", ".*").replace("?", ".")
        return bool(re.fullmatch(regex, name, re.IGNORECASE))

    def _should_include(self, rel_path: str) -> bool:
        name = os.path.basename(rel_path)
        for pat in self.exclude:
            if self._match_pattern(name, pat) or self._match_pattern(rel_path, pat):
                return False
        if self.include:
            return any(
                self._match_pattern(name, p) or self._match_pattern(rel_path, p)
                for p in self.include
            )
        return True

    def _file_hash(self, filepath: str, block_size: int = 65536) -> str:
        h = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(block_size), b""):
                    h.update(chunk)
        except (IOError, OSError):
            return ""
        return h.hexdigest()

    def _files_equal(self, src_file: str, dst_file: str) -> bool:
        """比较两个文件是否相同"""
        try:
            src_stat = os.stat(src_file)
            dst_stat = os.stat(dst_file)
        except OSError:
            return False

        # 大小不同直接判定不同
        if src_stat.st_size != dst_stat.st_size:
            return False

        if self.use_hash:
            return self._file_hash(src_file) == self._file_hash(dst_file)

        # 默认对比 mtime（精度 1 秒）
        return int(src_stat.st_mtime) == int(dst_stat.st_mtime)

    def _scan(self, root: str) -> dict:
        """扫描目录，返回 {rel_path: stat}"""
        result = {}
        if not os.path.exists(root):
            return result

        for dirpath, dirs, filenames in os.walk(root):
            for fname in filenames:
                full = os.path.join(dirpath, fname)
                rel = os.path.relpath(full, root).replace("\\", "/")
                if self._should_include(rel):
                    try:
                        st = os.stat(full)
                        result[rel] = {"size": st.st_size, "mtime": st.st_mtime}
                    except OSError:
                        pass
        return result

    def diff(self) -> dict:
        """计算源与目标的差异（仅分析，不操作）"""
        src_files = self._scan(self.source)
        dst_files = self._scan(self.target)

        diff = {
            "only_in_source": [],
            "only_in_target": [],
            "modified": [],
            "identical": [],
        }

        for rel in src_files:
            if rel not in dst_files:
                diff["only_in_source"].append(rel)
            else:
                src_full = os.path.join(self.source, rel)
                dst_full = os.path.join(self.target, rel)
                if self._files_equal(src_full, dst_full):
                    diff["identical"].append(rel)
                else:
                    diff["modified"].append(rel)

        for rel in dst_files:
            if rel not in src_files:
                diff["only_in_target"].append(rel)

        return diff

    def sync(self) -> dict:
        """执行同步"""
        for k in self.actions:
            self.actions[k].clear()

        if not os.path.exists(self.source):
            self.actions["error"].append(f"源目录不存在: {self.source}")
            return self.actions

        if not self.dry_run:
            os.makedirs(self.target, exist_ok=True)

        src_files = self._scan(self.source)
        dst_files = self._scan(self.target)

        # 复制 / 更新
        for rel in src_files:
            src_full = os.path.join(self.source, rel)
            dst_full = os.path.join(self.target, rel)

            try:
                if rel not in dst_files:
                    # 新增
                    self._do_copy(src_full, dst_full)
                    self.actions["add"].append(rel)
                elif not self._files_equal(src_full, dst_full):
                    # 更新
                    self._do_copy(src_full, dst_full)
                    self.actions["update"].append(rel)
                else:
                    self.actions["skip"].append(rel)
            except (IOError, OSError) as e:
                self.actions["error"].append(f"{rel}: {e}")

        # 删除目标多余文件 (mirror 模式)
        if self.delete:
            for rel in dst_files:
                if rel not in src_files:
                    dst_full = os.path.join(self.target, rel)
                    try:
                        if not self.dry_run:
                            os.remove(dst_full)
                        self.actions["delete"].append(rel)
                    except OSError as e:
                        self.actions["error"].append(f"删除 {rel}: {e}")

            # 清理空目录
            if not self.dry_run:
                self._remove_empty_dirs(self.target)

        return self.actions

    def _do_copy(self, src: str, dst: str):
        """复制文件（保留元数据）"""
        if self.dry_run:
            return
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)

    def _remove_empty_dirs(self, root: str):
        """删除空目录"""
        for dirpath, dirs, files in os.walk(root, topdown=False):
            if dirpath == root:
                continue
            try:
                if not os.listdir(dirpath):
                    os.rmdir(dirpath)
            except OSError:
                pass

    def print_diff(self, diff: dict):
        """打印差异"""
        print("\n--- 目录差异 ---")
        print(f"  源 ({self.source})")
        print(f"  目标 ({self.target})")
        print(f"\n  仅在源:     {len(diff['only_in_source'])}")
        for f in diff["only_in_source"][:10]:
            print(f"    + {f}")
        print(f"\n  仅在目标:   {len(diff['only_in_target'])}")
        for f in diff["only_in_target"][:10]:
            print(f"    - {f}")
        print(f"\n  已修改:     {len(diff['modified'])}")
        for f in diff["modified"][:10]:
            print(f"    * {f}")
        print(f"\n  相同:       {len(diff['identical'])}")

    def print_report(self):
        """打印同步报告"""
        prefix = "[DRY-RUN] " if self.dry_run else ""
        print(f"\n--- {prefix}同步报告 ---")
        print(f"  源:     {self.source}")
        print(f"  目标:   {self.target}")
        print(f"  新增:   {len(self.actions['add'])}")
        for f in self.actions["add"][:10]:
            print(f"    + {f}")
        print(f"  更新:   {len(self.actions['update'])}")
        for f in self.actions["update"][:10]:
            print(f"    * {f}")
        print(f"  跳过:   {len(self.actions['skip'])}")
        print(f"  删除:   {len(self.actions['delete'])}")
        for f in self.actions["delete"][:10]:
            print(f"    - {f}")
        if self.actions["error"]:
            print(f"  错误:   {len(self.actions['error'])}")
            for e in self.actions["error"][:10]:
                print(f"    ! {e}")


# ==================== 演示 ====================


def write_file(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def setup_demo(demo_dir: str) -> tuple:
    """创建演示源/目标目录"""
    src = os.path.join(demo_dir, "source")
    dst = os.path.join(demo_dir, "target")

    # 清理之前
    for d in (src, dst):
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)

    # 源目录
    write_file(os.path.join(src, "README.md"), "# Project v1.0")
    write_file(os.path.join(src, "config.json"), '{"version": 1}')
    write_file(os.path.join(src, "code", "main.py"), 'print("v1")')
    write_file(os.path.join(src, "code", "utils.py"), "def add(a,b): return a+b")
    write_file(os.path.join(src, "docs", "intro.md"), "intro v1")
    write_file(os.path.join(src, "tmp", "cache.tmp"), "temp data")  # 应被排除

    return src, dst


def cleanup_demo(demo_dir: str):
    for sub in ["source", "target", "target2"]:
        p = os.path.join(demo_dir, sub)
        if os.path.exists(p):
            shutil.rmtree(p, ignore_errors=True)


if __name__ == "__main__":
    print("=" * 60)
    print("  文件同步工具 Demo")
    print("=" * 60)

    demo_dir = os.path.dirname(os.path.abspath(__file__))
    cleanup_demo(demo_dir)
    src, dst = setup_demo(demo_dir)

    try:
        # 1. 干跑预览
        print("\n>>> 1. 干跑预览（dry-run）")
        sync = FileSync(src, dst, exclude=["*.tmp"], dry_run=True)
        sync.sync()
        sync.print_report()

        # 2. 真实同步（首次）
        print("\n>>> 2. 真实首次同步")
        sync = FileSync(src, dst, exclude=["*.tmp"], dry_run=False)
        sync.sync()
        sync.print_report()

        # 3. 修改源后再次同步
        print("\n>>> 3. 修改源后增量同步")
        write_file(os.path.join(src, "README.md"), "# Project v2.0")  # 修改
        write_file(os.path.join(src, "code", "new.py"), "# new file")  # 新增
        os.remove(os.path.join(src, "docs", "intro.md"))  # 删除

        # 让 mtime 不同
        import time as _t

        _t.sleep(1.1)
        os.utime(os.path.join(src, "README.md"), None)

        sync = FileSync(src, dst, exclude=["*.tmp"])
        sync.sync()
        sync.print_report()
        print(
            "  注: 源已删除 docs/intro.md，但默认未启用 delete，目标仍保留。"
        )

        # 4. mirror 模式（同步删除）
        print("\n>>> 4. Mirror 模式（同步删除）")
        sync = FileSync(src, dst, exclude=["*.tmp"], delete=True)
        sync.sync()
        sync.print_report()

        # 5. 差异报告
        print("\n>>> 5. 差异分析")
        # 在 target 中添加一个本地文件
        write_file(os.path.join(dst, "local_only.txt"), "local")
        sync = FileSync(src, dst, exclude=["*.tmp"])
        diff = sync.diff()
        sync.print_diff(diff)

        # 6. 使用 hash 比对
        print("\n>>> 6. 使用 hash 比对（精确但较慢）")
        sync = FileSync(src, dst, exclude=["*.tmp"], use_hash=True)
        diff = sync.diff()
        print(
            f"  identical={len(diff['identical'])} "
            f"modified={len(diff['modified'])} "
            f"only_src={len(diff['only_in_source'])} "
            f"only_dst={len(diff['only_in_target'])}"
        )

        # 7. include 模式：仅同步特定文件
        print("\n>>> 7. 仅同步 *.py 到 target2")
        target2 = os.path.join(demo_dir, "target2")
        sync = FileSync(src, target2, include=["*.py"])
        sync.sync()
        sync.print_report()

    finally:
        cleanup_demo(demo_dir)

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
