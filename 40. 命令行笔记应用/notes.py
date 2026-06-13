"""
命令行笔记应用
功能：基于命令行的笔记应用，支持创建、查看、编辑、删除笔记，
      标签管理、全文搜索、置顶/收藏、Markdown 导出、版本历史、
      统计分析等
"""

import os
import re
import json
import uuid
import shutil
from datetime import datetime
from collections import Counter


class Note:
    """单条笔记"""

    def __init__(self, title: str, content: str = "", tags: list = None,
                 note_id: str = None, created: str = None,
                 updated: str = None, pinned: bool = False,
                 favorite: bool = False, history: list = None):
        self.id = note_id or uuid.uuid4().hex[:8]
        self.title = title
        self.content = content
        self.tags = tags or []
        now = datetime.now().isoformat(timespec="seconds")
        self.created = created or now
        self.updated = updated or now
        self.pinned = pinned
        self.favorite = favorite
        self.history = history or []  # 历史版本快照

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "tags": self.tags,
            "created": self.created,
            "updated": self.updated,
            "pinned": self.pinned,
            "favorite": self.favorite,
            "history": self.history,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Note":
        return cls(
            title=d["title"],
            content=d.get("content", ""),
            tags=d.get("tags", []),
            note_id=d.get("id"),
            created=d.get("created"),
            updated=d.get("updated"),
            pinned=d.get("pinned", False),
            favorite=d.get("favorite", False),
            history=d.get("history", []),
        )

    def update(self, title: str = None, content: str = None,
               tags: list = None):
        """更新笔记，并保存历史版本"""
        # 保存当前版本到历史
        self.history.append({
            "title": self.title,
            "content": self.content,
            "tags": list(self.tags),
            "saved_at": self.updated,
        })
        # 仅保留最近 10 个版本
        if len(self.history) > 10:
            self.history = self.history[-10:]

        if title is not None:
            self.title = title
        if content is not None:
            self.content = content
        if tags is not None:
            self.tags = tags
        self.updated = datetime.now().isoformat(timespec="seconds")

    def add_tags(self, tags: list):
        for t in tags:
            t = t.strip()
            if t and t not in self.tags:
                self.tags.append(t)
        self.updated = datetime.now().isoformat(timespec="seconds")

    def remove_tags(self, tags: list):
        for t in tags:
            if t in self.tags:
                self.tags.remove(t)
        self.updated = datetime.now().isoformat(timespec="seconds")

    @property
    def word_count(self) -> int:
        # 中英文均按字符计算（去空白）
        return len(re.sub(r"\s+", "", self.content))

    @property
    def preview(self) -> str:
        text = self.content.replace("\n", " ").strip()
        return text[:50] + ("..." if len(text) > 50 else "")


class NotesApp:
    """笔记应用"""

    def __init__(self, data_file: str = "notes.json"):
        self.data_file = data_file
        self.notes = {}  # id -> Note
        self.load()

    # ==================== 持久化 ====================

    def load(self):
        if not os.path.exists(self.data_file):
            return
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for nd in data.get("notes", []):
                note = Note.from_dict(nd)
                self.notes[note.id] = note
        except (json.JSONDecodeError, KeyError) as e:
            print(f"[警告] 加载失败: {e}")

    def save(self):
        data = {
            "notes": [n.to_dict() for n in self.notes.values()],
            "saved_at": datetime.now().isoformat(),
        }
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ==================== CRUD ====================

    def create(self, title: str, content: str = "",
               tags: list = None) -> Note:
        if not title.strip():
            raise ValueError("标题不能为空")
        note = Note(title.strip(), content, tags or [])
        self.notes[note.id] = note
        self.save()
        return note

    def get(self, note_id: str) -> Note:
        if note_id not in self.notes:
            raise KeyError(f"笔记 {note_id} 不存在")
        return self.notes[note_id]

    def update(self, note_id: str, **kwargs) -> Note:
        note = self.get(note_id)
        note.update(**kwargs)
        self.save()
        return note

    def delete(self, note_id: str) -> bool:
        if note_id in self.notes:
            del self.notes[note_id]
            self.save()
            return True
        return False

    def toggle_pin(self, note_id: str) -> bool:
        note = self.get(note_id)
        note.pinned = not note.pinned
        note.updated = datetime.now().isoformat(timespec="seconds")
        self.save()
        return note.pinned

    def toggle_favorite(self, note_id: str) -> bool:
        note = self.get(note_id)
        note.favorite = not note.favorite
        note.updated = datetime.now().isoformat(timespec="seconds")
        self.save()
        return note.favorite

    # ==================== 列表 / 排序 ====================

    def list_all(self, sort_by: str = "updated", reverse: bool = True,
                 only_pinned: bool = False,
                 only_favorite: bool = False) -> list:
        """列出笔记
        sort_by: updated/created/title
        """
        notes = list(self.notes.values())
        if only_pinned:
            notes = [n for n in notes if n.pinned]
        if only_favorite:
            notes = [n for n in notes if n.favorite]

        # 置顶笔记永远在前
        sort_func = {
            "updated": lambda n: n.updated,
            "created": lambda n: n.created,
            "title": lambda n: n.title,
        }.get(sort_by, lambda n: n.updated)

        notes.sort(key=sort_func, reverse=reverse)
        # 置顶分组
        pinned = [n for n in notes if n.pinned]
        normal = [n for n in notes if not n.pinned]
        return pinned + normal

    # ==================== 搜索 ====================

    def search(self, keyword: str, in_title: bool = True,
               in_content: bool = True, in_tags: bool = True,
               case_sensitive: bool = False) -> list:
        if not keyword:
            return []
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            pattern = re.compile(keyword, flags)
        except re.error:
            pattern = re.compile(re.escape(keyword), flags)

        results = []
        for note in self.notes.values():
            matched = False
            if in_title and pattern.search(note.title):
                matched = True
            elif in_content and pattern.search(note.content):
                matched = True
            elif in_tags and any(pattern.search(t) for t in note.tags):
                matched = True
            if matched:
                results.append(note)
        # 按更新时间排序
        results.sort(key=lambda n: n.updated, reverse=True)
        return results

    def search_by_tag(self, tag: str) -> list:
        return [n for n in self.notes.values() if tag in n.tags]

    # ==================== 标签管理 ====================

    def all_tags(self) -> dict:
        """统计所有标签出现次数"""
        counter = Counter()
        for note in self.notes.values():
            counter.update(note.tags)
        return dict(counter)

    def rename_tag(self, old_tag: str, new_tag: str) -> int:
        count = 0
        for note in self.notes.values():
            if old_tag in note.tags:
                note.tags = [new_tag if t == old_tag else t for t in note.tags]
                # 去重
                seen = set()
                note.tags = [t for t in note.tags
                            if not (t in seen or seen.add(t))]
                note.updated = datetime.now().isoformat(timespec="seconds")
                count += 1
        if count:
            self.save()
        return count

    # ==================== 历史版本 ====================

    def get_history(self, note_id: str) -> list:
        return self.get(note_id).history

    def revert(self, note_id: str, version_index: int) -> Note:
        """回滚到指定版本（从历史快照恢复）"""
        note = self.get(note_id)
        if version_index < 0 or version_index >= len(note.history):
            raise IndexError("版本不存在")
        snapshot = note.history[version_index]
        note.update(
            title=snapshot["title"],
            content=snapshot["content"],
            tags=list(snapshot["tags"]),
        )
        return note

    # ==================== 导入导出 ====================

    def export_markdown(self, note_id: str, filepath: str):
        """单条笔记导出为 Markdown"""
        note = self.get(note_id)
        lines = [
            f"# {note.title}",
            "",
            f"- 创建时间: {note.created}",
            f"- 更新时间: {note.updated}",
        ]
        if note.tags:
            lines.append(f"- 标签: {', '.join('`' + t + '`' for t in note.tags)}")
        lines.extend(["", "---", "", note.content, ""])
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def export_all_markdown(self, dir_path: str) -> int:
        os.makedirs(dir_path, exist_ok=True)
        count = 0
        for note in self.notes.values():
            safe_title = re.sub(r'[<>:"/\\|?*]', "_", note.title)[:50]
            fname = f"{note.id}_{safe_title}.md"
            self.export_markdown(note.id, os.path.join(dir_path, fname))
            count += 1
        return count

    def import_markdown(self, filepath: str) -> Note:
        """导入 Markdown 文件作为笔记"""
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
        # 第一行 # 标题
        title_match = re.match(r"^#\s+(.+)$", text, re.MULTILINE)
        title = title_match.group(1) if title_match else os.path.basename(filepath)
        # 简单提取正文（去掉首部元信息）
        content = text
        if "---" in content:
            content = content.split("---", 1)[1].strip()
        return self.create(title, content)

    # ==================== 统计 ====================

    def stats(self) -> dict:
        notes = list(self.notes.values())
        total_words = sum(n.word_count for n in notes)
        return {
            "total_notes": len(notes),
            "total_words": total_words,
            "pinned": sum(1 for n in notes if n.pinned),
            "favorite": sum(1 for n in notes if n.favorite),
            "total_tags": len(self.all_tags()),
            "avg_words": (total_words // len(notes)) if notes else 0,
            "longest": max((n for n in notes), key=lambda n: n.word_count,
                           default=None),
        }

    # ==================== 显示 ====================

    @staticmethod
    def print_list(notes: list, title: str = "笔记列表"):
        print(f"\n--- {title} ({len(notes)}) ---")
        if not notes:
            print("  (空)")
            return
        for note in notes:
            marks = ""
            if note.pinned:
                marks += "[置顶] "
            if note.favorite:
                marks += "[收藏] "
            tags = " ".join(f"#{t}" for t in note.tags)
            print(f"  [{note.id}] {marks}{note.title}")
            print(f"     更新: {note.updated} | {tags}")
            if note.content:
                print(f"     {note.preview}")

    @staticmethod
    def print_note(note: Note):
        print(f"\n{'=' * 60}")
        marks = []
        if note.pinned:
            marks.append("置顶")
        if note.favorite:
            marks.append("收藏")
        mark_str = f"[{' '.join(marks)}] " if marks else ""
        print(f"{mark_str}{note.title}  ({note.id})")
        print(f"创建: {note.created}    更新: {note.updated}")
        if note.tags:
            print(f"标签: {', '.join(note.tags)}")
        print(f"字数: {note.word_count}")
        print("-" * 60)
        print(note.content)
        print("=" * 60)


# ==================== CLI 交互 ====================

def interactive_cli(app: NotesApp):
    """交互式命令行"""
    print("\n命令: new, list, view, edit, delete, pin, fav, "
          "search, tag, stats, export, quit")
    while True:
        try:
            cmd = input("\n> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break
        if cmd in ("quit", "q", "exit"):
            break

        try:
            if cmd == "new":
                title = input("标题: ").strip()
                print("内容（输入空行结束）:")
                lines = []
                while True:
                    line = input()
                    if not line:
                        break
                    lines.append(line)
                tags = input("标签（逗号分隔）: ").strip()
                tag_list = [t.strip() for t in tags.split(",") if t.strip()]
                note = app.create(title, "\n".join(lines), tag_list)
                print(f"已创建笔记 {note.id}")
            elif cmd == "list":
                NotesApp.print_list(app.list_all(), "全部笔记")
            elif cmd.startswith("view"):
                nid = input("ID: ").strip()
                NotesApp.print_note(app.get(nid))
            elif cmd.startswith("search"):
                kw = input("关键词: ").strip()
                NotesApp.print_list(app.search(kw), f"搜索 '{kw}'")
            elif cmd == "stats":
                for k, v in app.stats().items():
                    print(f"  {k}: {v}")
            elif cmd == "delete":
                nid = input("ID: ").strip()
                print("已删除" if app.delete(nid) else "未找到")
            elif cmd == "pin":
                nid = input("ID: ").strip()
                state = app.toggle_pin(nid)
                print(f"置顶状态: {state}")
            else:
                print("未知命令")
        except (KeyError, ValueError, IndexError) as e:
            print(f"错误: {e}")


# ==================== 演示 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("  命令行笔记应用 Demo")
    print("=" * 60)

    base_dir = os.path.dirname(__file__)
    data_file = os.path.join(base_dir, "demo_notes.json")
    md_dir = os.path.join(base_dir, "demo_md_export")

    # 清理旧数据
    if os.path.exists(data_file):
        os.remove(data_file)
    if os.path.exists(md_dir):
        shutil.rmtree(md_dir)

    app = NotesApp(data_file)

    # 1. 创建笔记
    print("\n--- 1. 创建笔记 ---")
    n1 = app.create(
        "Python 学习要点",
        "1. 基础语法\n2. 面向对象\n3. 标准库\n4. 异常处理\n5. 装饰器和生成器",
        tags=["编程", "Python", "学习"],
    )
    n2 = app.create(
        "周末购物清单",
        "- 牛奶\n- 鸡蛋\n- 面包\n- 水果\n- 蔬菜",
        tags=["生活", "购物"],
    )
    n3 = app.create(
        "项目开发 TODO",
        "[ ] 完成 API 设计\n[ ] 数据库迁移\n[ ] 单元测试\n[x] 需求评审",
        tags=["工作", "项目"],
    )
    n4 = app.create(
        "读书笔记 - 三体",
        "黑暗森林法则：宇宙就是一座黑暗的森林，每一个文明都是带枪的猎人。",
        tags=["读书", "科幻"],
    )
    n5 = app.create(
        "Python 装饰器",
        "装饰器本质上是一个函数，它接受一个函数作为参数并返回一个新的函数。"
        "常见用途：日志记录、权限校验、性能测试、缓存等。",
        tags=["编程", "Python", "进阶"],
    )
    print(f"已创建 {len(app.notes)} 条笔记")

    # 2. 列出
    NotesApp.print_list(app.list_all(), "全部笔记")

    # 3. 查看单条
    print("\n--- 3. 查看笔记详情 ---")
    NotesApp.print_note(n1)

    # 4. 编辑笔记（含历史）
    print("\n--- 4. 编辑笔记 ---")
    app.update(n1.id, content=n1.content + "\n6. 元类与反射")
    app.update(n1.id, tags=n1.tags + ["进阶"])
    print(f"笔记 {n1.id} 已更新，历史版本数: {len(n1.history)}")
    NotesApp.print_note(n1)

    # 5. 置顶 / 收藏
    print("\n--- 5. 置顶和收藏 ---")
    app.toggle_pin(n3.id)
    app.toggle_favorite(n5.id)
    app.toggle_favorite(n1.id)
    NotesApp.print_list(app.list_all(), "排序后（置顶在前）")

    # 6. 搜索
    print("\n--- 6. 搜索 ---")
    NotesApp.print_list(app.search("Python"), "搜索 'Python'")
    NotesApp.print_list(app.search("项目"), "搜索 '项目'")

    # 7. 按标签
    print("\n--- 7. 按标签查询 ---")
    NotesApp.print_list(app.search_by_tag("编程"), "标签 #编程")

    # 8. 标签统计
    print("\n--- 8. 标签统计 ---")
    for tag, count in sorted(app.all_tags().items(), key=lambda x: -x[1]):
        print(f"  #{tag:<10} {count}")

    # 9. 重命名标签
    print("\n--- 9. 重命名标签 '学习' -> '笔记' ---")
    n = app.rename_tag("学习", "笔记")
    print(f"影响 {n} 条笔记")
    print(f"现在的标签: {list(app.all_tags().keys())}")

    # 10. 历史版本
    print("\n--- 10. 历史版本 ---")
    history = app.get_history(n1.id)
    print(f"笔记 {n1.id} 共有 {len(history)} 个历史版本")
    for i, h in enumerate(history):
        print(f"  v{i}: {h['saved_at']} - 标题: {h['title']}, "
              f"内容字数: {len(h['content'])}")

    # 11. 回滚
    print("\n--- 11. 回滚到第一个版本 ---")
    app.revert(n1.id, 0)
    print(f"回滚后内容长度: {len(n1.content)} 字符")

    # 12. 导出 Markdown
    print("\n--- 12. 导出 Markdown ---")
    count = app.export_all_markdown(md_dir)
    print(f"已导出 {count} 个 .md 文件至 {md_dir}")
    files = sorted(os.listdir(md_dir))[:3]
    for f in files:
        print(f"  - {f}")
    # 展示一个
    sample = os.path.join(md_dir, files[0])
    print(f"\n示例 ({files[0]}):")
    with open(sample, "r", encoding="utf-8") as f:
        print(f.read())

    # 13. 删除笔记
    print("\n--- 13. 删除笔记 ---")
    app.delete(n2.id)
    print(f"已删除 {n2.id}, 剩余 {len(app.notes)} 条")

    # 14. 统计
    print("\n--- 14. 笔记统计 ---")
    s = app.stats()
    print(f"  总笔记数:  {s['total_notes']}")
    print(f"  总字数:    {s['total_words']}")
    print(f"  置顶:      {s['pinned']}")
    print(f"  收藏:      {s['favorite']}")
    print(f"  标签数:    {s['total_tags']}")
    print(f"  平均字数:  {s['avg_words']}")
    if s['longest']:
        print(f"  最长笔记:  [{s['longest'].id}] {s['longest'].title} "
              f"({s['longest'].word_count} 字)")

    # 15. 持久化验证
    print("\n--- 15. 持久化验证 ---")
    app2 = NotesApp(data_file)
    print(f"重新加载后笔记数: {len(app2.notes)}")

    # 清理
    if os.path.exists(data_file):
        os.remove(data_file)
    if os.path.exists(md_dir):
        shutil.rmtree(md_dir)

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
    print("\n要进入交互模式：")
    print("  app = NotesApp('my_notes.json'); interactive_cli(app)")
