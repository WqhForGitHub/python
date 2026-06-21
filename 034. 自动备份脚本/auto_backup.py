"""
自动备份脚本
功能：
    - 全量备份指定目录到 ZIP 归档（带时间戳）
    - 支持 include/exclude 通配符过滤
    - 支持增量备份（仅打包修改时间在某时间后的文件）
    - 自动清理旧备份（按数量或天数）
    - 生成备份元数据（JSON 清单 + SHA256 校验）
    - 验证备份文件完整性
"""

import os
import re
import json
import zipfile
import hashlib
import shutil
from datetime import datetime, timedelta


class BackupManager:
    """备份管理器"""

    def __init__(self, source: str, backup_dir: str):
        self.source = os.path.abspath(source)
        self.backup_dir = os.path.abspath(backup_dir)
        os.makedirs(self.backup_dir, exist_ok=True)

    # -------- 核心备份 --------
    def backup(
        self,
        include=None,
        exclude=None,
        since: datetime = None,
        compress=True,
        name_prefix="backup",
    ) -> dict:
        """执行一次备份

        include / exclude: 通配符列表（如 ['*.py', '*.txt']）
        since: 仅备份 mtime > since 的文件（增量）
        """
        if not os.path.isdir(self.source):
            raise FileNotFoundError(f"源目录不存在: {self.source}")

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        kind = "incr" if since else "full"
        zip_name = f"{name_prefix}_{kind}_{ts}.zip"
        zip_path = os.path.join(self.backup_dir, zip_name)

        files_to_backup = []
        for root, dirs, files in os.walk(self.source):
            for fname in files:
                fp = os.path.join(root, fname)
                rel = os.path.relpath(fp, self.source)

                if include and not any(self._match(rel, p) for p in include):
                    continue
                if exclude and any(self._match(rel, p) for p in exclude):
                    continue

                if since:
                    try:
                        mtime = datetime.fromtimestamp(os.path.getmtime(fp))
                        if mtime <= since:
                            continue
                    except OSError:
                        continue

                files_to_backup.append((fp, rel))

        if not files_to_backup:
            print(f"  无文件需要备份")
            return {
                "zip": None,
                "kind": kind,
                "files": 0,
                "size": 0,
                "manifest": None,
            }

        compression = zipfile.ZIP_DEFLATED if compress else zipfile.ZIP_STORED
        manifest = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "source": self.source,
            "kind": kind,
            "since": since.isoformat() if since else None,
            "files": [],
        }

        with zipfile.ZipFile(zip_path, "w", compression) as zf:
            for fp, rel in files_to_backup:
                try:
                    zf.write(fp, arcname=rel)
                    sha = self._sha256(fp)
                    manifest["files"].append(
                        {
                            "path": rel.replace("\\", "/"),
                            "size": os.path.getsize(fp),
                            "sha256": sha,
                            "mtime": datetime.fromtimestamp(
                                os.path.getmtime(fp)
                            ).isoformat(timespec="seconds"),
                        }
                    )
                except (IOError, OSError) as e:
                    print(f"  跳过: {rel} ({e})")

            # 写入清单
            zf.writestr("MANIFEST.json", json.dumps(manifest, ensure_ascii=False, indent=2))

        size = os.path.getsize(zip_path)
        return {
            "zip": zip_path,
            "kind": kind,
            "files": len(manifest["files"]),
            "size": size,
            "manifest": manifest,
        }

    # -------- 校验 --------
    def verify(self, zip_path: str) -> dict:
        """校验备份文件完整性"""
        result = {"ok": True, "errors": [], "checked": 0}
        if not os.path.isfile(zip_path):
            result["ok"] = False
            result["errors"].append("文件不存在")
            return result

        with zipfile.ZipFile(zip_path, "r") as zf:
            # ZIP 自带 CRC 校验
            bad = zf.testzip()
            if bad:
                result["ok"] = False
                result["errors"].append(f"损坏文件: {bad}")

            try:
                manifest = json.loads(zf.read("MANIFEST.json").decode("utf-8"))
            except KeyError:
                result["errors"].append("缺少 MANIFEST.json")
                return result

            for entry in manifest["files"]:
                path = entry["path"]
                try:
                    data = zf.read(path)
                except KeyError:
                    result["ok"] = False
                    result["errors"].append(f"缺失: {path}")
                    continue
                actual = hashlib.sha256(data).hexdigest()
                result["checked"] += 1
                if actual != entry["sha256"]:
                    result["ok"] = False
                    result["errors"].append(f"哈希不匹配: {path}")

        return result

    # -------- 还原 --------
    def restore(self, zip_path: str, target_dir: str):
        """从备份还原到指定目录"""
        os.makedirs(target_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            for name in zf.namelist():
                if name == "MANIFEST.json":
                    continue
                zf.extract(name, target_dir)
        return target_dir

    # -------- 清理旧备份 --------
    def cleanup(self, keep_count: int = None, keep_days: int = None) -> list:
        """清理旧备份"""
        backups = sorted(
            [
                os.path.join(self.backup_dir, f)
                for f in os.listdir(self.backup_dir)
                if f.endswith(".zip")
            ],
            key=os.path.getmtime,
            reverse=True,
        )

        removed = []
        if keep_count is not None and len(backups) > keep_count:
            for fp in backups[keep_count:]:
                os.remove(fp)
                removed.append(fp)
            backups = backups[:keep_count]

        if keep_days is not None:
            cutoff = datetime.now() - timedelta(days=keep_days)
            for fp in backups[:]:
                mtime = datetime.fromtimestamp(os.path.getmtime(fp))
                if mtime < cutoff:
                    os.remove(fp)
                    removed.append(fp)

        return removed

    # -------- 列出备份 --------
    def list_backups(self) -> list:
        items = []
        for f in sorted(os.listdir(self.backup_dir)):
            if not f.endswith(".zip"):
                continue
            fp = os.path.join(self.backup_dir, f)
            items.append(
                {
                    "name": f,
                    "size": os.path.getsize(fp),
                    "mtime": datetime.fromtimestamp(os.path.getmtime(fp)),
                }
            )
        return items

    # -------- 工具 --------
    def _sha256(self, filepath: str) -> str:
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def _match(self, name: str, pattern: str) -> bool:
        regex = (
            re.escape(pattern).replace(r"\*", ".*").replace(r"\?", ".")
        )
        return bool(re.fullmatch(regex, name.replace("\\", "/"), re.IGNORECASE))


# ==================== Demo ====================


def create_demo_data(base_dir: str):
    """创建演示数据"""
    src = os.path.join(base_dir, "data")
    os.makedirs(os.path.join(src, "docs"), exist_ok=True)
    os.makedirs(os.path.join(src, "logs"), exist_ok=True)

    files = {
        "readme.txt": "项目说明",
        "config.json": '{"version":"1.0"}',
        "docs/manual.md": "# 用户手册",
        "docs/api.md": "# API 文档",
        "logs/app.log": "[INFO] started",
        "logs/error.log": "[ERROR] oops",
        "tmp.cache": "临时缓存（应排除）",
    }
    for rel, content in files.items():
        fp = os.path.join(src, rel)
        with open(fp, "w", encoding="utf-8") as f:
            f.write(content)
    return src


if __name__ == "__main__":
    print("=" * 60)
    print("  自动备份脚本 Demo")
    print("=" * 60)

    base = os.path.dirname(os.path.abspath(__file__))
    source = create_demo_data(base)
    backup_dir = os.path.join(base, "backups")
    restore_dir = os.path.join(base, "restored")

    mgr = BackupManager(source, backup_dir)

    # 1. 全量备份
    print("\n--- 1. 全量备份（排除 *.cache） ---")
    info = mgr.backup(exclude=["*.cache"])
    print(f"  备份文件: {os.path.basename(info['zip'])}")
    print(f"  类型:     {info['kind']}")
    print(f"  文件数:   {info['files']}")
    print(f"  大小:     {info['size']} 字节")

    # 2. 校验
    print("\n--- 2. 完整性校验 ---")
    v = mgr.verify(info["zip"])
    print(f"  通过:   {v['ok']}")
    print(f"  校验数: {v['checked']}")
    if v["errors"]:
        for e in v["errors"]:
            print(f"  错误:   {e}")

    # 3. 修改文件后做增量
    print("\n--- 3. 修改文件 + 增量备份 ---")
    import time as _t
    _t.sleep(1)
    since = datetime.now() - timedelta(seconds=2)
    with open(os.path.join(source, "logs", "app.log"), "a", encoding="utf-8") as f:
        f.write("\n[INFO] new entry")
    incr = mgr.backup(since=since, exclude=["*.cache"], name_prefix="myapp")
    print(f"  增量备份: {os.path.basename(incr['zip']) if incr['zip'] else '(无变更)'}")
    print(f"  文件数:   {incr['files']}")
    if incr["manifest"]:
        for f in incr["manifest"]["files"]:
            print(f"    + {f['path']}")

    # 4. 列出备份
    print("\n--- 4. 备份列表 ---")
    for b in mgr.list_backups():
        print(f"  {b['name']:<45} {b['size']:>6} 字节  {b['mtime']}")

    # 5. 还原
    print("\n--- 5. 从备份还原 ---")
    mgr.restore(info["zip"], restore_dir)
    restored_files = []
    for r, _, fs in os.walk(restore_dir):
        for fn in fs:
            restored_files.append(os.path.relpath(os.path.join(r, fn), restore_dir))
    print(f"  还原到: {restore_dir}")
    print(f"  共还原 {len(restored_files)} 个文件:")
    for f in sorted(restored_files):
        print(f"    - {f}")

    # 6. 清理（仅保留 1 个）
    print("\n--- 6. 清理旧备份（保留最新 1 个） ---")
    removed = mgr.cleanup(keep_count=1)
    for r in removed:
        print(f"  删除: {os.path.basename(r)}")
    print(f"  剩余: {[b['name'] for b in mgr.list_backups()]}")

    # 清理 demo 文件
    shutil.rmtree(source, ignore_errors=True)
    shutil.rmtree(backup_dir, ignore_errors=True)
    shutil.rmtree(restore_dir, ignore_errors=True)

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
