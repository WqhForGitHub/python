"""
石头剪刀布
玩家与电脑对战，支持多局计分、连胜记录、历史回放
"""

import random

# ── 常量定义 ────────────────────────────────────────────────
CHOICES = {
    "1": "石头",
    "2": "剪刀",
    "3": "布",
}

# 胜负关系：key 胜 value
WINS_OVER = {
    "石头": "剪刀",
    "剪刀": "布",
    "布": "石头",
}

EMOJI = {
    "石头": "✊",
    "剪刀": "✌️",
    "布": "🖐️",
}


# ── 核心逻辑 ────────────────────────────────────────────────
def judge(player: str, computer: str) -> str:
    """判断胜负，返回 'win' / 'lose' / 'draw'"""
    if player == computer:
        return "draw"
    if WINS_OVER[player] == computer:
        return "win"
    return "lose"


def get_computer_choice() -> str:
    """电脑随机出拳"""
    return random.choice(list(CHOICES.values()))


def get_player_choice() -> str | None:
    """获取玩家输入，返回出拳名称或 None（退出）"""
    while True:
        print("\n  请出拳：")
        print("  1. ✊ 石头")
        print("  2. ✌️ 剪刀")
        print("  3. 🖐️ 布")
        print("  q. 退出游戏")

        choice = input("\n  你的选择: ").strip().lower()

        if choice == "q":
            return None
        if choice in CHOICES:
            return CHOICES[choice]
        print("  无效输入，请重新选择。")


# ── 模式选择 ────────────────────────────────────────────────
def mode_single() -> None:
    """单局模式"""
    print("\n── 单局对战 ──")
    player = get_player_choice()
    if player is None:
        return

    computer = get_computer_choice()
    result = judge(player, computer)

    print(f"\n  你出了 {EMOJI[player]} {player}，电脑出了 {EMOJI[computer]} {computer}")
    _print_result(result)


def mode_best_of(rounds: int) -> None:
    """N 局胜者模式（先赢 rounds 局者获胜）"""
    print(f"\n── 三局两胜制（先赢 {rounds} 局获胜）──")

    p_wins = 0
    c_wins = 0
    round_num = 0
    history = []

    while p_wins < rounds and c_wins < rounds:
        round_num += 1
        print(f"\n  ── 第 {round_num} 局 ──  (你 {p_wins} : {c_wins} 电脑)")
        player = get_player_choice()
        if player is None:
            print("\n  游戏中断。")
            return

        computer = get_computer_choice()
        result = judge(player, computer)
        history.append((round_num, player, computer, result))

        print(
            f"\n  你出了 {EMOJI[player]} {player}，电脑出了 {EMOJI[computer]} {computer}"
        )
        _print_result(result)

        if result == "win":
            p_wins += 1
        elif result == "lose":
            c_wins += 1

    # 最终结果
    print("\n" + "=" * 40)
    if p_wins > c_wins:
        print(f"  🎉 你赢了！最终比分 {p_wins} : {c_wins}")
    else:
        print(f"  😢 电脑赢了！最终比分 {p_wins} : {c_wins}")
    print("=" * 40)

    # 回放
    _show_history(history)


def mode_endless() -> None:
    """无尽模式，持续对战直到退出"""
    print("\n── 无尽对战 ──")
    print("  输入 q 随时退出\n")

    stats = {"win": 0, "lose": 0, "draw": 0}
    streak = 0  # 当前连胜
    max_streak = 0  # 最高连胜
    history = []
    round_num = 0

    while True:
        round_num += 1
        print(
            f"\n  ── 第 {round_num} 局 ──  (胜 {stats['win']} / 负 {stats['lose']} / 平 {stats['draw']})"
            f"  连胜: {streak}"
        )

        player = get_player_choice()
        if player is None:
            break

        computer = get_computer_choice()
        result = judge(player, computer)
        history.append((round_num, player, computer, result))

        print(
            f"\n  你出了 {EMOJI[player]} {player}，电脑出了 {EMOJI[computer]} {computer}"
        )
        _print_result(result)

        stats[result] += 1
        if result == "win":
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0

    # 结算
    total = sum(stats.values())
    if total > 0:
        print("\n" + "=" * 40)
        print("  对战统计")
        print("=" * 40)
        print(f"  总局数:   {total}")
        print(f"  胜:       {stats['win']}  ({stats['win'] / total:.1%})")
        print(f"  负:       {stats['lose']}  ({stats['lose'] / total:.1%})")
        print(f"  平:       {stats['draw']}  ({stats['draw'] / total:.1%})")
        print(f"  最高连胜: {max_streak}")
        print("=" * 40)
        _show_history(history)
    else:
        print("\n  未进行任何对局，再见！")


# ── 辅助函数 ────────────────────────────────────────────────
def _print_result(result: str) -> None:
    """打印单局结果"""
    if result == "win":
        print("  ✅ 你赢了！")
    elif result == "lose":
        print("  ❌ 你输了！")
    else:
        print("  🤝 平局！")


def _show_history(history: list) -> None:
    """展示对局历史"""
    if not history:
        return
    show = input("\n  查看对局记录？(y/n，默认n): ").strip().lower()
    if show != "y":
        return

    print("\n  局号  |  你      |  电脑    |  结果")
    print("  " + "-" * 40)
    result_map = {"win": "胜", "lose": "负", "draw": "平"}
    for rnd, player, computer, result in history:
        print(
            f"  {rnd:<5} | {EMOJI[player]} {player:<4} | {EMOJI[computer]} {computer:<4} | {result_map[result]}"
        )


# ── 主菜单 ──────────────────────────────────────────────────
def main() -> None:
    print("=" * 40)
    print("       石头剪刀布")
    print("=" * 40)
    print("\n  选择游戏模式：")
    print("  1. 单局对战")
    print("  2. 三局两胜")
    print("  3. 无尽对战")
    print("  q. 退出")

    while True:
        mode = input("\n  请选择 (1/2/3/q): ").strip().lower()

        if mode == "1":
            mode_single()
        elif mode == "2":
            mode_best_of(2)
        elif mode == "3":
            mode_endless()
        elif mode == "q":
            print("\n  再见！")
            break
        else:
            print("  无效输入，请重新选择。")
            continue

        # 一轮结束后询问是否继续
        again = input("\n  返回主菜单？(y/n，默认y): ").strip().lower()
        if again == "n":
            print("\n  再见！")
            break


if __name__ == "__main__":
    main()
