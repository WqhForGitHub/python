"""
简单通讯录（字典存储）
使用字典在内存中存储联系人信息，
支持增删改查、搜索、导入导出等功能。
"""

import json
import sys
from datetime import datetime

# ── 数据存储 ──────────────────────────────────────────────


class ContactBook:
    """基于字典的通讯录。"""

    def __init__(self):
        self.contacts: dict[str, dict] = {}  # name -> info
        self._next_id = 1

    def add(
        self, name: str, phone: str, email: str = "", address: str = "", note: str = ""
    ) -> bool:
        """添加联系人。"""
        if name in self.contacts:
            print(f"  联系人 '{name}' 已存在")
            return False
        self.contacts[name] = {
            "id": self._next_id,
            "phone": phone,
            "email": email,
            "address": address,
            "note": note,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        self._next_id += 1
        print(f"  已添加联系人：{name}")
        return True

    def delete(self, name: str) -> bool:
        """删除联系人。"""
        if name in self.contacts:
            del self.contacts[name]
            print(f"  已删除联系人：{name}")
            return True
        print(f"  联系人 '{name}' 不存在")
        return False

    def update(self, name: str, field: str, value: str) -> bool:
        """更新联系人信息。"""
        if name not in self.contacts:
            print(f"  联系人 '{name}' 不存在")
            return False
        if field in ("phone", "email", "address", "note"):
            self.contacts[name][field] = value
            print(f"  已更新 {name} 的 {field}")
            return True
        elif field == "name":
            # 改名
            self.contacts[value] = self.contacts.pop(name)
            print(f"  已将 '{name}' 改名为 '{value}'")
            return True
        print(f"  无效字段：{field}")
        return False

    def search(self, keyword: str) -> list[tuple[str, dict]]:
        """按关键词搜索联系人。"""
        keyword = keyword.lower()
        results = []
        for name, info in self.contacts.items():
            if (
                keyword in name.lower()
                or keyword in info["phone"]
                or keyword in info.get("email", "").lower()
                or keyword in info.get("address", "").lower()
                or keyword in info.get("note", "").lower()
            ):
                results.append((name, info))
        return results

    def list_all(self) -> list[tuple[str, dict]]:
        """列出所有联系人。"""
        return sorted(self.contacts.items(), key=lambda x: x[1].get("id", 0))

    def show(self, name: str) -> None:
        """展示联系人详情。"""
        if name not in self.contacts:
            print(f"  联系人 '{name}' 不存在")
            return
        info = self.contacts[name]
        print(f"\n  ═══ {name} ═══")
        print(f"  电话：{info['phone']}")
        print(f"  邮箱：{info.get('email', '（无）')}")
        print(f"  地址：{info.get('address', '（无）')}")
        print(f"  备注：{info.get('note', '（无）')}")
        print(f"  创建：{info.get('created', '（未知）')}")
        print()

    def export_json(self, path: str) -> None:
        """导出为 JSON 文件。"""
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.contacts, f, ensure_ascii=False, indent=2)
            print(f"  已导出 {len(self.contacts)} 个联系人到 {path}")
        except Exception as e:
            print(f"  导出失败：{e}")

    def import_json(self, path: str) -> None:
        """从 JSON 文件导入。"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            count = 0
            for name, info in data.items():
                if name not in self.contacts:
                    self.contacts[name] = info
                    count += 1
            print(f"  已导入 {count} 个联系人（跳过 {len(data) - count} 个已存在）")
        except FileNotFoundError:
            print(f"  文件不存在：{path}")
        except json.JSONDecodeError:
            print("  JSON 格式错误")
        except Exception as e:
            print(f"  导入失败：{e}")


# ── 展示函数 ──────────────────────────────────────────────


def show_list(contacts: list[tuple[str, dict]]) -> None:
    """以表格形式展示联系人列表。"""
    if not contacts:
        print("  无联系人")
        return
    print(f"\n  {'序号':<4s} {'姓名':<10s} {'电话':<15s} {'邮箱':<20s}")
    print(f"  {'─' * 4} {'─' * 10} {'─' * 15} {'─' * 20}")
    for i, (name, info) in enumerate(contacts, 1):
        print(
            f"  {i:<4d} {name:<10s} {info['phone']:<15s} {info.get('email', ''):<20s}"
        )
    print()


# ── 主菜单 ────────────────────────────────────────────────


def print_menu() -> None:
    print("=" * 45)
    print("  简单通讯录")
    print("=" * 45)
    print("  1. 添加联系人")
    print("  2. 删除联系人")
    print("  3. 修改联系人")
    print("  4. 查看联系人详情")
    print("  5. 搜索联系人")
    print("  6. 列出所有联系人")
    print("  7. 导入通讯录（JSON）")
    print("  8. 导出通讯录（JSON）")
    print("  q. 退出")
    print("-" * 45)


def main() -> None:
    book = ContactBook()

    while True:
        print_menu()
        choice = input("  请选择: ").strip()

        if choice == "q":
            print("  再见！")
            break

        elif choice == "1":
            name = input("  姓名: ").strip()
            if not name:
                print("  姓名不能为空")
                continue
            phone = input("  电话: ").strip()
            if not phone:
                print("  电话不能为空")
                continue
            email = input("  邮箱（可选）: ").strip()
            address = input("  地址（可选）: ").strip()
            note = input("  备注（可选）: ").strip()
            book.add(name, phone, email, address, note)

        elif choice == "2":
            name = input("  要删除的联系人姓名: ").strip()
            if name:
                confirm = input(f"  确认删除 {name}？(y/N): ").strip().lower()
                if confirm == "y":
                    book.delete(name)

        elif choice == "3":
            name = input("  要修改的联系人姓名: ").strip()
            if name not in book.contacts:
                print(f"  联系人 '{name}' 不存在")
                continue
            print("  可修改字段：name / phone / email / address / note")
            field = input("  字段: ").strip().lower()
            value = input("  新值: ").strip()
            if value:
                book.update(name, field, value)

        elif choice == "4":
            name = input("  联系人姓名: ").strip()
            if name:
                book.show(name)

        elif choice == "5":
            keyword = input("  搜索关键词: ").strip()
            if keyword:
                results = book.search(keyword)
                if results:
                    show_list(results)
                else:
                    print("  未找到匹配的联系人")

        elif choice == "6":
            all_contacts = book.list_all()
            if all_contacts:
                show_list(all_contacts)
            else:
                print("  通讯录为空")

        elif choice == "7":
            path = input("  JSON 文件路径: ").strip()
            if path:
                book.import_json(path)

        elif choice == "8":
            path = input("  导出路径: ").strip()
            if path:
                book.export_json(path)

        else:
            print("  无效选择，请重新输入")


if __name__ == "__main__":
    main()
