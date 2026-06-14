"""
文件同步工具
功能：
    - 比较源目录和目标目录的差异（新增 / 修改 / 删除）
    - 支持单向 mirror 同步（让 dst 完全等于 src）
    - 支持双向同步（基于上次同步状态文件）
    - 支持 dry-run 预览模式（不实际操作）
    - 通过 SHA256 / 大小 / mtime 检测变更
    - 排除指定模式的文件
"""

import os
import re
import json
import shutil
import hashlib
from datetime import datetime


class FileSync:
    """文件同步工具"""

    def __init__(self, src: str, dst: str, exclude=None, use_hash=False):
        self.src = os.path.abspath(src)
        self.dst = os.path.abspath(dst)
        self.exclude = exclude or []
        self.use_hash = use_hash

    # -------- 扫描 --------
    def _scan(self, root: str) -> dict:
        """扫描目录，返回 {相对路径: {size, mtime, hash?}}"""
        index = {}
        if not os.path.isdir(root):
            return index
        for cur, dirs, files in os.walk(root):
            for fn in files:
                fp = os.path.join(cur, fn)
                rel = os.path.relpath(fp, root).replace("\\", "/")
                if any(self._match(rel, p) for p in self.exclude):
                    continue
                try:
                    st = os.stat(fp)
                except OSError:
                    continue
                entry = {"size": st.st_size, "mtime": int(st.st_mtime)}
                if self.use_hash:
                    entry["hash"] = self._sha256(fp)
                index[rel] = entry
        return index

    def _match(self, name: str, pattern: str) -> bool:
        regex = re.escape(pattern).replace(r"\*", ".*").replace(r"\?", ".")
        return bool(re.fullmatch(regex, name, re.IGNORECASE))

    def _sha256(self, fp: str) -> str:
        h = hashlib.sha256()
        try:
            with open(fp, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
        except OSError:
            return ""
        return h.hexdigest()

    # -------- 比较 --------
    def diff(self) -> dict:
        """比较两个目录"""
        src_idx = self._scan(self.src)
        dst_idx = self._scan(self.dst)

        added = []     # 仅 src 有
        removed = []   # 仅 dst 有
        modified = []  # 两边都有但不同
        same = []      # 一致

        for rel, s in src_idx.items():
            if rel not in dst_idx:
                added.append(rel)
            else:
                d = dst_idx[rel]
                if self._is_changed(s, d):
                    modified.append(rel)
                else:
                    same.append(rel)
        for rel in dst_idx:
            if rel not in src_idx:
                removed.append(rel)

        return {
            "added": sorted(added),
            "removed": sorted(removed),
            "modified": sorted(modified),
            "same": sorted(same),
            "src_count": len(src_idx),
            "dst_count": len(dst_idx),
        }

    def _is_changed(self, a: dict, b: dict) -> bool:
        if self.use_hash and "hash" in a and "hash" in b:
            return a["hash"] != b["hash"]
        if a["size"] != b["size"]:
            return True
        if abs(a["mtime"] - b["mtime"]) > 2:  # 容忍 2 秒差异
            return True
        return False

    # -------- 单向镜像同步 --------
    def mirror(self, dry_run=False, delete=True) -> dict:
        """让 dst 完全等于 src"""
        if not os.path.isdir(self.src):
            raise FileNotFoundError(self.src)
        os.makedirs(self.dst, exist_ok=True)

        d = self.diff()
        actions = []

        # 复制新增 + 修改
        for rel in d["added"] + d["modified"]:
            sp = os.path.join(self.src, rel)
            tp = os.path.join(self.dst, rel)
            actions.append(("copy", rel))
            if not dry_run:
                os.makedirs(os.path.dirname(tp), exist_ok=True)
                shutil.copy2(sp, tp)

        # 删除多余
        if delete:
            for rel in d["removed"]:
                tp = os.path.join(self.dst, rel)
                actions.append(("delete", rel))
                if not dry_run:
                    try:
                        os.remove(tp)
                    except OSError:
                        pass

            # 清理空目录
            if not dry_run:
                self._remove_empty_dirs(self.dst)

        return {
            "dry_run": dry_run,
            "copied": len(d["added"]) + len(d["modified"]),
            "deleted": len(d["removed"]) if delete else 0,
            "unchanged": len(d["same"]),
            "actions": actions,
        }

    # -------- 双向同步 --------
    def bidirectional(self, state_file: str, dry_run=False) -> dict:
        """双向同步（基于上一次状态）

        - 若文件仅在一侧新增 -> 复制到另一侧
        - 若两侧都修改了 -> 选择较新的，记录冲突
        """
        prev = {}
        if os.path.isfile(state_file):
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    prev = json.load(f)
            except (json.JSONDecodeError, OSError):
                prev = {}

        src_idx = self._scan(self.src)
        dst_idx = self._scan(self.dst)
        all_keys = set(src_idx) | set(dst_idx) | set(prev)

        actions = []
        conflicts = []

        for rel in all_keys:
            in_src = rel in src_idx
            in_dst = rel in dst_idx
            in_prev = rel in prev

            sp = os.path.join(self.src, rel)
            tp = os.path.join(self.dst, rel)

            if in_src and in_dst:
                if not self._is_changed(src_idx[rel], dst_idx[rel]):
                    continue
                # 双方都修改 -> 取较新者
                src_changed = (
                    not in_prev or self._is_changed(src_idx[rel], prev[rel])
                )
                dst_changed = (
                    not in_prev or self._is_changed(dst_idx[rel], prev[rel])
                )
                if src_changed and dst_changed:
                    conflicts.append(rel)
                    if src_idx[rel]["mtime"] >= dst_idx[rel]["mtime"]:
                        actions.append(("src->dst", rel))
                        if not dry_run:
                            shutil.copy2(sp, tp)
                    else:
                        actions.append(("dst->src", rel))
                        if not dry_run:
                            shutil.copy2(tp, sp)
                elif src_changed:
                    actions.append(("src->dst", rel))
                    if not dry_run:
                        shutil.copy2(sp, tp)
                else:
                    actions.append(("dst->src", rel))
                    if not dry_run:
                        shutil.copy2(tp, sp)
            elif in_src and not in_dst:
                if in_prev and not self._is_changed(src_idx[rel], prev[rel]):
                    # src 不变但 dst 被删 -> 删 src
                    actions.append(("delete src", rel))
                    if not dry_run:
                        try:
                            os.remove(sp)
                        except OSError:
                            pass
                else:
                    actions.append(("src->dst", rel))
                    if not dry_run:
                        os.makedirs(os.path.dirname(tp), exist_ok=True)
                        shutil.copy2(sp, tp)
            elif in_dst and not in_src:
                if in_prev and not self._is_changed(dst_idx[rel], prev[rel]):
                    actions.append(("delete dst", rel))
                    if not dry_run:
                        try:
                            os.remove(tp)
                        except OSError:
                            pass
                else:
                    actions.append(("dst->src", rel))
                    if not dry_run:
                        os.makedirs(os.path.dirname(sp), exist_ok=True)
                        shutil.copy2(tp, sp)

        # 保存新状态
        if not dry_run:
            new_state = self._scan(self.src)  # 同步后两侧应一致
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(new_state, f, ensure_ascii=False, indent=2)
            self._remove_empty_dirs(self.src)
            self._remove_empty_dirs(self.dst)

        return {"actions": actions, "conflicts": conflicts, "dry_run": dry_run}

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


def make_file(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def show_tree(root: str, label: str):
    print(f"  [{label}] {root}")
    if not os.path.isdir(root):
        print("    (不存在)")
        return
    items = []
    for cur, dirs, files in os.walk(root):
        for fn in files:
            fp = os.path.join(cur, fn)
            rel = os.path.relpath(fp, root)
            items.append(rel)
    for it in sorted(items):
        print(f"    - {it}")
    if not items:
        print("    (空)")


if __name__ == "__main__":
    print("=" * 60)
    print("  文件同步工具 Demo")
    print("=" * 60)

    base = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(base, "src_dir")
    dst = os.path.join(base, "dst_dir")

    # 清理上次残留
    for d in (src, dst):
        if os.path.exists(d):
            shutil.rmtree(d)

    # 准备初始数据
    make_file(os.path.join(src, "a.txt"), "AAA")
    make_file(os.path.join(src, "b.txt"), "BBB")
    make_file(os.path.join(src, "sub/c.txt"), "CCC")
    make_file(os.path.join(dst, "a.txt"), "AAA-old")
    make_file(os.path.join(dst, "old.txt"), "应被删除")

    sync = FileSync(src, dst, exclude=["*.tmp"], use_hash=True)

    # 1. 比较差异
    print("\n--- 1. 差异比较 ---")
    show_tree(src, "源")
    show_tree(dst, "目标")
    d = sync.diff()
    print(f"  新增({len(d['added'])}):    {d['added']}")
    print(f"  删除({len(d['removed'])}):  {d['removed']}")
    print(f"  修改({len(d['modified'])}): {d['modified']}")
    print(f"  一致({len(d['same'])}):    {d['same']}")

    # 2. dry-run 预览
    print("\n--- 2. Dry-run 预览镜像同步 ---")
    res = sync.mirror(dry_run=True)
    for act, rel in res["actions"]:
        print(f"  [{act}] {rel}")

    # 3. 实际镜像同步
    print("\n--- 3. 执行镜像同步 ---")
    res = sync.mirror(dry_run=False)
    print(f"  复制: {res['copied']}, 删除: {res['deleted']}, 未变: {res['unchanged']}")
    show_tree(dst, "目标(同步后)")

    # 4. 双向同步演示
    print("\n--- 4. 双向同步演示 ---")
    state_file = os.path.join(base, ".sync_state.json")
    if os.path.exists(state_file):
        os.remove(state_file)

    # 初始同步建立状态
    sync.bidirectional(state_file)
    # 双方各自做一些改动
    make_file(os.path.join(src, "new_in_src.txt"), "源新增")
    make_file(os.path.join(dst, "new_in_dst.txt"), "目标新增")
    with open(os.path.join(src, "b.txt"), "w", encoding="utf-8") as f:
        f.write("B 被源修改了")

    res = sync.bidirectional(state_file)
    print("  动作:")
    for act, rel in res["actions"]:
        print(f"    [{act}] {rel}")
    if res["conflicts"]:
        print(f"  冲突: {res['conflicts']}")
    show_tree(src, "源(双向后)")
    show_tree(dst, "目标(双向后)")

    # 清理
    shutil.rmtree(src, ignore_errors=True)
    shutil.rmtree(dst, ignore_errors=True)
    if os.path.exists(state_file):
        os.remove(state_file)

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
