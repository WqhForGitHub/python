"""
文本版冒险游戏
在一个奇幻世界中进行探索、战斗、收集，
通过选择推进剧情，体验文字冒险的乐趣。
"""

import random
import sys

# ── 游戏数据 ──────────────────────────────────────────────

ENEMIES = {
    "森林": [
        {"name": "野狼", "hp": 20, "atk": 5, "exp": 10, "gold": 5},
        {"name": "毒蛇", "hp": 15, "atk": 8, "exp": 12, "gold": 3},
        {"name": "哥布林", "hp": 25, "atk": 6, "exp": 15, "gold": 8},
    ],
    "洞穴": [
        {"name": "蝙蝠", "hp": 12, "atk": 4, "exp": 8, "gold": 3},
        {"name": "石像鬼", "hp": 35, "atk": 10, "exp": 25, "gold": 15},
        {"name": "巨蛛", "hp": 30, "atk": 8, "exp": 20, "gold": 10},
    ],
    "遗迹": [
        {"name": "骷髅兵", "hp": 30, "atk": 9, "exp": 20, "gold": 12},
        {"name": "暗影", "hp": 40, "atk": 12, "exp": 30, "gold": 20},
        {"name": "巫妖", "hp": 50, "atk": 15, "exp": 50, "gold": 30},
    ],
}

ITEMS = {
    "治疗药水": {"type": "heal", "value": 30, "price": 15},
    "大治疗药水": {"type": "heal", "value": 60, "price": 30},
    "力量药水": {"type": "atk_up", "value": 5, "price": 25},
    "防御药水": {"type": "def_up", "value": 3, "price": 20},
    "铁剑": {"type": "weapon", "value": 8, "price": 50},
    "钢剑": {"type": "weapon", "value": 15, "price": 120},
    "皮甲": {"type": "armor", "value": 5, "price": 40},
    "铁甲": {"type": "armor", "value": 12, "price": 100},
}

SHOP_ITEMS = [
    "治疗药水",
    "大治疗药水",
    "力量药水",
    "防御药水",
    "铁剑",
    "钢剑",
    "皮甲",
    "铁甲",
]

EVENTS = [
    "你发现了一个宝箱，获得了一些金币！",
    "你遇到了一个旅人，他给了你一瓶药水。",
    "你发现了一处清泉，恢复了生命值。",
    "你踩到了陷阱，受到了伤害！",
    "你发现了一块古老的石碑，上面刻着神秘的文字。",
    "你遇到了一个商人，他向你兜售物品。",
    "你发现了一朵奇异的花，散发着微光。",
]

# ── 玩家类 ────────────────────────────────────────────────


class Player:
    """玩家角色。"""

    def __init__(self, name: str):
        self.name = name
        self.hp = 100
        self.max_hp = 100
        self.atk = 10
        self.defense = 3
        self.gold = 30
        self.exp = 0
        self.level = 1
        self.inventory: dict[str, int] = {"治疗药水": 2}
        self.weapon = "木剑"
        self.armor = "布衣"
        self.location = "村庄"

    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, dmg: int) -> int:
        """受到伤害，返回实际伤害。"""
        actual = max(1, dmg - self.defense)
        self.hp = max(0, self.hp - actual)
        return actual

    def heal(self, amount: int) -> None:
        """治疗。"""
        self.hp = min(self.max_hp, self.hp + amount)

    def gain_exp(self, amount: int) -> None:
        """获得经验值，检查升级。"""
        self.exp += amount
        needed = self.level * 50
        if self.exp >= needed:
            self.exp -= needed
            self.level += 1
            self.max_hp += 15
            self.hp = self.max_hp
            self.atk += 3
            self.defense += 1
            print(f"\n  升级！你现在是 {self.level} 级！")
            print(f"  生命上限 +15  攻击 +3  防御 +1")

    def add_item(self, item: str, count: int = 1) -> None:
        self.inventory[item] = self.inventory.get(item, 0) + count

    def remove_item(self, item: str, count: int = 1) -> bool:
        if self.inventory.get(item, 0) >= count:
            self.inventory[item] -= count
            if self.inventory[item] <= 0:
                del self.inventory[item]
            return True
        return False

    def show_status(self) -> None:
        """展示玩家状态。"""
        hp_bar = self._bar(self.hp, self.max_hp)
        exp_needed = self.level * 50
        exp_bar = self._bar(self.exp, exp_needed)

        print(f"\n  ═══ {self.name} 的状态 ═══")
        print(f"  等级：{self.level}")
        print(f"  生命：{hp_bar} {self.hp}/{self.max_hp}")
        print(f"  经验：{exp_bar} {self.exp}/{exp_needed}")
        print(f"  攻击：{self.atk}  防御：{self.defense}")
        print(f"  金币：{self.gold}")
        print(f"  武器：{self.weapon}  护甲：{self.armor}")
        print(f"  位置：{self.location}")
        if self.inventory:
            print(f"  背包：{', '.join(f'{k}x{v}' for k, v in self.inventory.items())}")
        print()

    def _bar(self, current: int, maximum: int, width: int = 15) -> str:
        filled = int(current / maximum * width) if maximum > 0 else 0
        return "█" * filled + "░" * (width - filled)


# ── 战斗系统 ──────────────────────────────────────────────


def battle(player: Player, enemy: dict) -> bool:
    """进行战斗，返回是否胜利。"""
    enemy_hp = enemy["hp"]
    enemy_name = enemy["name"]
    enemy_atk = enemy["atk"]

    print(f"\n  遭遇了 {enemy_name}！")
    print(f"  敌人生命：{enemy_hp}  攻击：{enemy_atk}")

    while player.is_alive() and enemy_hp > 0:
        print(
            f"\n  [{player.name} HP:{player.hp}/{player.max_hp}]  "
            f"[{enemy_name} HP:{enemy_hp}]"
        )
        print("  1. 攻击  2. 使用物品  3. 逃跑")

        choice = input("  行动: ").strip()

        if choice == "1":
            # 玩家攻击
            dmg = player.atk + random.randint(-2, 3)
            crit = random.random() < 0.15
            if crit:
                dmg = int(dmg * 1.8)
                print(f"  暴击！对 {enemy_name} 造成 {dmg} 点伤害！")
            else:
                print(f"  对 {enemy_name} 造成 {dmg} 点伤害")
            enemy_hp = max(0, enemy_hp - dmg)

            if enemy_hp <= 0:
                break

            # 敌人反击
            actual = player.take_damage(enemy_atk + random.randint(-1, 2))
            print(f"  {enemy_name} 对你造成 {actual} 点伤害")

        elif choice == "2":
            # 使用物品
            usable = {
                k: v
                for k, v in player.inventory.items()
                if ITEMS.get(k, {}).get("type") in ("heal", "atk_up", "def_up")
            }
            if not usable:
                print("  没有可用的物品")
                continue
            print("  可用物品：")
            for i, (name, count) in enumerate(usable.items(), 1):
                print(f"    {i}. {name} x{count}")
            raw = input("  使用哪个（编号，0取消）: ").strip()
            try:
                idx = int(raw)
                if idx == 0:
                    continue
                item_name = list(usable.keys())[idx - 1]
                use_item(player, item_name)
            except (ValueError, IndexError):
                print("  无效选择")

        elif choice == "3":
            if random.random() < 0.5:
                print("  成功逃跑！")
                return False
            else:
                print("  逃跑失败！")
                actual = player.take_damage(enemy_atk)
                print(f"  {enemy_name} 对你造成 {actual} 点伤害")

    if player.is_alive():
        print(f"\n  战胜了 {enemy_name}！")
        print(f"  获得 {enemy['exp']} 经验、{enemy['gold']} 金币")
        player.gain_exp(enemy["exp"])
        player.gold += enemy["gold"]
        return True
    else:
        print(f"\n  你被 {enemy_name} 击败了...")
        return False


# ── 物品使用 ──────────────────────────────────────────────


def use_item(player: Player, item_name: str) -> None:
    """使用物品。"""
    item = ITEMS.get(item_name)
    if not item:
        return

    if not player.remove_item(item_name):
        print(f"  你没有 {item_name}")
        return

    if item["type"] == "heal":
        player.heal(item["value"])
        print(f"  使用了 {item_name}，恢复 {item['value']} 生命值")
    elif item["type"] == "atk_up":
        player.atk += item["value"]
        print(f"  使用了 {item_name}，攻击力 +{item['value']}")
    elif item["type"] == "def_up":
        player.defense += item["value"]
        print(f"  使用了 {item_name}，防御力 +{item['value']}")


# ── 商店 ──────────────────────────────────────────────────


def shop(player: Player) -> None:
    """商店系统。"""
    print(f"\n  ═══ 商店 ═══  你的金币：{player.gold}")
    for i, name in enumerate(SHOP_ITEMS, 1):
        item = ITEMS[name]
        desc = ""
        if item["type"] == "heal":
            desc = f"恢复 {item['value']} HP"
        elif item["type"] == "weapon":
            desc = f"攻击 +{item['value']}"
        elif item["type"] == "armor":
            desc = f"防御 +{item['value']}"
        elif item["type"] == "atk_up":
            desc = f"攻击 +{item['value']}（临时）"
        elif item["type"] == "def_up":
            desc = f"防御 +{item['value']}（临时）"
        print(f"  {i}. {name:<8s} - {desc:<16s} {item['price']} 金币")

    print(f"  0. 离开商店")

    while True:
        raw = input("  购买（编号）: ").strip()
        if raw == "0":
            break
        try:
            idx = int(raw)
            if 1 <= idx <= len(SHOP_ITEMS):
                item_name = SHOP_ITEMS[idx - 1]
                item = ITEMS[item_name]
                if player.gold >= item["price"]:
                    player.gold -= item["price"]
                    if item["type"] == "weapon":
                        player.weapon = item_name
                        player.atk += item["value"]
                        print(f"  装备了 {item_name}！攻击力 +{item['value']}")
                    elif item["type"] == "armor":
                        player.armor = item_name
                        player.defense += item["value"]
                        print(f"  装备了 {item_name}！防御力 +{item['value']}")
                    else:
                        player.add_item(item_name)
                        print(f"  购买了 {item_name}")
                else:
                    print("  金币不足！")
            else:
                print("  无效选择")
        except ValueError:
            print("  请输入编号")


# ── 探索系统 ──────────────────────────────────────────────


def explore(player: Player, area: str) -> None:
    """探索指定区域。"""
    player.location = area

    if area not in ENEMIES:
        print("  未知区域")
        return

    roll = random.random()

    if roll < 0.5:
        # 遭遇敌人
        enemy = random.choice(ENEMIES[area])
        battle(player, enemy)
    elif roll < 0.75:
        # 随机事件
        event = random.choice(EVENTS)
        print(f"\n  {event}")
        if "金币" in event:
            gold = random.randint(5, 20)
            player.gold += gold
            print(f"  获得 {gold} 金币！")
        elif "药水" in event:
            player.add_item("治疗药水")
            print(f"  获得治疗药水！")
        elif "清泉" in event:
            heal = random.randint(10, 30)
            player.heal(heal)
            print(f"  恢复了 {heal} 生命值")
        elif "陷阱" in event:
            dmg = random.randint(5, 15)
            player.take_damage(dmg)
            print(f"  受到了 {dmg} 点伤害")
    else:
        # 安全通过
        print(f"\n  你在{area}中探索了一番，没有遇到危险。")
        exp = random.randint(3, 8)
        player.gain_exp(exp)
        print(f"  获得了 {exp} 点经验")


# ── 主菜单 ────────────────────────────────────────────────


def print_menu(player: Player) -> None:
    print("=" * 45)
    print(f"  文本冒险游戏    {player.name} Lv.{player.level}")
    print("=" * 45)
    print("  1. 查看状态")
    print("  2. 探索森林")
    print("  3. 探索洞穴")
    print("  4. 探索遗迹")
    print("  5. 休息（恢复生命）")
    print("  6. 使用物品")
    print("  7. 商店")
    print("  q. 退出游戏")
    print("-" * 45)


def main() -> None:
    print("=" * 45)
    print("  欢迎来到文本冒险游戏！")
    print("=" * 45)

    name = input("  请输入你的名字: ").strip()
    if not name:
        name = "勇者"

    player = Player(name)
    print(f"\n  {name}，你的冒险开始了！")
    print("  你从村庄出发，面前有三个方向：")
    print("  神秘的森林、幽深的洞穴、古老的遗迹。")

    while player.is_alive():
        print_menu(player)
        choice = input("  请选择: ").strip()

        if choice == "q":
            print("  退出游戏，再见！")
            break

        elif choice == "1":
            player.show_status()

        elif choice == "2":
            explore(player, "森林")

        elif choice == "3":
            if player.level < 3:
                print("  洞穴危险重重，建议 3 级以上再进入")
                confirm = input("  仍然要进入吗？(y/N): ").strip().lower()
                if confirm != "y":
                    continue
            explore(player, "洞穴")

        elif choice == "4":
            if player.level < 5:
                print("  遗迹中潜伏着强大的敌人，建议 5 级以上再进入")
                confirm = input("  仍然要进入吗？(y/N): ").strip().lower()
                if confirm != "y":
                    continue
            explore(player, "遗迹")

        elif choice == "5":
            heal = player.max_hp // 2
            player.heal(heal)
            player.gold = max(0, player.gold - 5)
            print(f"  你在旅店休息了一晚，恢复了 {heal} 生命值（花费 5 金币）")

        elif choice == "6":
            usable = {
                k: v
                for k, v in player.inventory.items()
                if ITEMS.get(k, {}).get("type") in ("heal", "atk_up", "def_up")
            }
            if not usable:
                print("  背包中没有可用的物品")
                continue
            for i, (name, count) in enumerate(usable.items(), 1):
                print(f"  {i}. {name} x{count}")
            raw = input("  使用哪个（编号，0取消）: ").strip()
            try:
                idx = int(raw)
                if idx > 0:
                    item_name = list(usable.keys())[idx - 1]
                    use_item(player, item_name)
            except (ValueError, IndexError):
                pass

        elif choice == "7":
            shop(player)

        else:
            print("  无效选择")

        if not player.is_alive():
            print(f"\n  {player.name} 倒下了...")
            print(f"  最终等级：{player.level}  金币：{player.gold}")
            print("  游戏结束。")
            break

        if player.level >= 10:
            print(f"\n  恭喜！{player.name} 达到了 10 级，成为了传奇冒险者！")
            print("  你通关了！")
            break


if __name__ == "__main__":
    main()
