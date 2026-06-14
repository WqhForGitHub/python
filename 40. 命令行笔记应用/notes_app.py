"""
命令行笔记应用
功能：
    - 创建/查看/编辑/删除笔记
    - 支持标签、置顶
    - 全文搜索（关键词、标签筛选）
    - 按时间排序、按更新时间排序
    - JSON 持久化
    - 导出为 Markdown
"""

import os
import json
import uuid
from datetime import datetime


class Note:
    def __init__(self, title: str, content: str = "", tags=None,
                 nid: str = None, pinned: bool = False,
                 created_at: str = None, updated_at: str = None):
        self.id = nid or uuid.uuid4().hex[:8]
        self.title = title
        self.content = content
        self.tags = tags or []
        self.pinned = pinned
        self.created_at = created_at or datetime.now().isoformat(timespec="seconds")
        self.updated_at = updated_at or self.created_at

    def to_dict(self):
        return {
            "id": self.id, "title": self.title, "content": self.content,
            "tags": self.tags, "pinned": self.pinned,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            title=d["title"], content=d.get("content", ""),
            tags=d.get("tags", []), nid=d.get("id"),
            pinned=d.get("pinned", False),
            created_at=d.get("created_at"), updated_at=d.get("updated_at"),
        )


class NoteApp:
    def __init__(self, filepath: str = "notes.json"):
        self.filepath = filepath
        self.notes: list[Note] = []
        self._load()

    # -------- 持久化 --------
    def _load(self):
        if os.path.isfile(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.notes = [Note.from_dict(d) for d in data]
            except (json.JSONDecodeError, OSError):
                self.notes = []

    def save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump([n.to_dict() for n in self.notes], f,
                      ensure_ascii=False, indent=2)

    # -------- CRUD --------
    def add(self, title: str, content: str = "", tags=None,
            pinned: bool = False) -> Note:
        note = Note(title=title, content=content, tags=tags or [], pinned=pinned)
        self.notes.append(note)
        self.save()
        return note

    def get(self, nid: str):
        for n in self.notes:
            if n.id == nid:
                return n
        return None

    def update(self, nid: str, title: str = None, content: str = None,
               tags=None, pinned: bool = None) -> bool:
        n = self.get(nid)
        if not n:
            return False
        if title is not None:
            n.title = title
        if content is not None:
            n.content = content
        if tags is not None:
            n.tags = tags
        if pinned is not None:
            n.pinned = pinned
        n.updated_at = datetime.now().isoformat(timespec="seconds")
        self.save()
        return True

    def delete(self, nid: str) -> bool:
        before = len(self.notes)
        self.notes = [n for n in self.notes if n.id != nid]
        if len(self.notes) < before:
            self.save()
            return True
        return False

    # -------- 查询 --------
    def list(self, sort_by: str = "updated") -> list:
        notes = list(self.notes)
        # 置顶优先, 然后按时间倒序
        key = "updated_at" if sort_by == "updated" else "created_at"
        notes.sort(key=lambda n: (not n.pinned, ""), reverse=False)
        notes.sort(key=lambda n: getattr(n, key), reverse=True)
        notes.sort(key=lambda n: not n.pinned)
        return notes

    def search(self, keyword: str = "", tag: str = "") -> list:
        kw = keyword.lower()
        out = []
        for n in self.notes:
            if tag and tag not in n.tags:
                continue
            if kw and kw not in n.title.lower() and kw not in n.content.lower():
                continue
            out.append(n)
        return out

    def all_tags(self) -> dict:
        cnt = {}
        for n in self.notes:
            for t in n.tags:
                cnt[t] = cnt.get(t, 0) + 1
        return dict(sorted(cnt.items(), key=lambda x: -x[1]))

    # -------- 导出 --------
    def export_markdown(self, path: str):
        lines = ["# 我的笔记", ""]
        for n in self.list():
            star = "[置顶] " if n.pinned else ""
            tags = " ".join(f"#{t}" for t in n.tags)
            lines += [
                f"## {star}{n.title}",
                f"*更新于 {n.updated_at}*  {tags}",
                "",
                n.content,
                "",
                "---",
                "",
            ]
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))


# ==================== Demo ====================

def show_note(n: Note, full: bool = False):
    pin = "[*]" if n.pinned else "   "
    tags = ", ".join(n.tags) if n.tags else "-"
    print(f"  {pin} [{n.id}] {n.title}")
    print(f"      标签: {tags}   更新: {n.updated_at}")
    if full and n.content:
        for line in n.content.splitlines():
            print(f"      | {line}")


if __name__ == "__main__":
    print("=" * 60)
    print("  命令行笔记应用 Demo")
    print("=" * 60)

    base = os.path.dirname(os.path.abspath(__file__))
    db = os.path.join(base, "demo_notes.json")
    md = os.path.join(base, "demo_notes_export.md")
    if os.path.exists(db):
        os.remove(db)

    app = NoteApp(db)

    # 1. 添加笔记
    print("\n--- 1. 添加笔记 ---")
    app.add("Python 切片速记",
            "list[a:b:c] 表示从 a 到 b 步长 c\n负数表示倒序",
            tags=["python", "速查"], pinned=True)
    app.add("待买清单",
            "- 牛奶\n- 鸡蛋\n- 面包",
            tags=["生活"])
    app.add("学习计划",
            "1. 每天 30 分钟算法\n2. 每周完成一个 demo",
            tags=["计划", "学习"])
    app.add("Git 常用命令",
            "git status\ngit log --oneline\ngit reset --hard HEAD~1",
            tags=["git", "速查"])
    print(f"  共 {len(app.notes)} 条笔记")

    # 2. 列表
    print("\n--- 2. 列表（置顶优先） ---")
    for n in app.list():
        show_note(n)

    # 3. 全文搜索
    print("\n--- 3. 搜索 'git' ---")
    for n in app.search("git"):
        show_note(n, full=True)

    # 4. 按标签筛选
    print("\n--- 4. 按标签筛选 '速查' ---")
    for n in app.search(tag="速查"):
        show_note(n)

    # 5. 标签统计
    print("\n--- 5. 标签统计 ---")
    for t, c in app.all_tags().items():
        print(f"  #{t}: {c}")

    # 6. 修改 / 删除
    print("\n--- 6. 修改 + 删除 ---")
    first = app.notes[0]
    app.update(first.id, content=first.content + "\n(补充：可省略部分参数)")
    print(f"  修改 {first.id} 的内容")
    last = app.notes[-1]
    app.delete(last.id)
    print(f"  删除 {last.id}, 剩余 {len(app.notes)} 条")

    # 7. 导出
    print("\n--- 7. 导出 Markdown ---")
    app.export_markdown(md)
    size = os.path.getsize(md)
    print(f"  已导出: {md}  ({size} bytes)")

    # 清理
    for f in (db, md):
        if os.path.exists(f):
            os.remove(f)

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
