"""
终端小游戏（猜词）
系统随机选择一个单词，玩家逐字母猜测，
类似 Hangman 游戏，支持难度选择和统计。
"""

import random
import sys

# ── 词库定义 ──────────────────────────────────────────────

WORD_BANK = {
    "easy": [
        "cat",
        "dog",
        "sun",
        "moon",
        "fish",
        "bird",
        "tree",
        "book",
        "rain",
        "snow",
        "star",
        "fire",
        "wind",
        "lake",
        "hill",
        "cake",
        "door",
        "hand",
        "foot",
        "love",
        "hope",
        "blue",
        "gold",
        "dark",
        "apple",
        "happy",
        "light",
        "water",
        "green",
        "music",
        "dream",
        "smile",
    ],
    "medium": [
        "python",
        "guitar",
        "jungle",
        "planet",
        "rocket",
        "bridge",
        "castle",
        "dragon",
        "forest",
        "island",
        "market",
        "orange",
        "palace",
        "rabbit",
        "silver",
        "temple",
        "valley",
        "winter",
        "camera",
        "dinner",
        "engine",
        "flower",
        "garden",
        "hammer",
    ],
    "hard": [
        "algorithm",
        "beautiful",
        "chocolate",
        "diamond",
        "elephant",
        "frequency",
        "gorgeous",
        "happiness",
        "important",
        "jellyfish",
        "knowledge",
        "landscape",
        "mysterious",
        "nightmare",
        "operation",
        "paragraph",
        "question",
        "raspberry",
        "structure",
        "treasure",
    ],
}

# ── HANGMAN 图案 ─────────────────────────────────────────

HANGMAN_STAGES = [
    [
        "  ┌─────┐",
        "  │     │",
        "  │",
        "  │",
        "  │",
        "  │",
        " ─┴─",
    ],
    [
        "  ┌─────┐",
        "  │     │",
        "  │     😐",
        "  │",
        "  │",
        "  │",
        " ─┴─",
    ],
    [
        "  ┌─────┐",
        "  │     │",
        "  │     😐",
        "  │     │",
        "  │",
        "  │",
        " ─┴─",
    ],
    [
        "  ┌─────┐",
        "  │     │",
        "  │     😐",
        "  │    /│",
        "  │",
        "  │",
        " ─┴─",
    ],
    [
        "  ┌─────┐",
        "  │     │",
        "  │     😐",
        "  │    /│\\",
        "  │",
        "  │",
        " ─┴─",
    ],
    [
        "  ┌─────┐",
        "  │     │",
        "  │     😐",
        "  │    /│\\",
        "  │    /",
        "  │",
        " ─┴─",
    ],
    [
        "  ┌─────┐",
        "  │     │",
        "  │     😵",
        "  │    /│\\",
        "  │    / \\",
        "  │",
        " ─┴─",
    ],
]

MAX_WRONG = len(HANGMAN_STAGES) - 1  # 6

# ── 游戏逻辑 ──────────────────────────────────────────────


class GuessWordGame:
    """猜词游戏。"""

    def __init__(self):
        self.wins = 0
        self.losses = 0
        self.streak = 0
        self.best_streak = 0

    def play(self, difficulty: str = "medium") -> None:
        """进行一局游戏。"""
        word = random.choice(WORD_BANK.get(difficulty, WORD_BANK["medium"]))
        word_lower = word.lower()
        guessed: set[str] = set()
        wrong_count = 0

        while wrong_count < MAX_WRONG:
            # 显示当前状态
            self._display(word_lower, guessed, wrong_count)

            # 获取输入
            letter = input("  猜一个字母（或输入 ! 提示, q 放弃）: ").strip().lower()

            if letter == "q":
                print(f"\n  放弃了！答案是：{word}\n")
                self._record_loss()
                return

            if letter == "!":
                # 给一个提示
                unrevealed = [c for c in word_lower if c not in guessed]
                if unrevealed:
                    hint = random.choice(unrevealed)
                    guessed.add(hint)
                    wrong_count += 1  # 提示消耗一次机会
                    print(f"  提示：字母 '{hint}' 在单词中")
                continue

            if len(letter) != 1 or not letter.isalpha():
                print("  请输入单个字母")
                continue

            if letter in guessed:
                print(f"  已经猜过 '{letter}' 了")
                continue

            guessed.add(letter)

            if letter in word_lower:
                print(f"  正确！'{letter}' 在单词中")
            else:
                wrong_count += 1
                print(f"  错误！'{letter}' 不在单词中（{wrong_count}/{MAX_WRONG}）")

            # 检查是否猜完
            if all(c in guessed for c in word_lower):
                self._display(word_lower, guessed, wrong_count)
                print(f"  恭喜！你猜出了：{word}\n")
                self._record_win()
                return

        # 用完所有机会
        print(HANGMAN_STAGES[-1])
        print(f"\n  游戏结束！答案是：{word}\n")
        self._record_loss()

    def _display(self, word: str, guessed: set[str], wrong: int) -> None:
        """显示游戏界面。"""
        print()
        print(HANGMAN_STAGES[wrong])
        # 显示单词
        display = " ".join(c if c in guessed else "_" for c in word)
        print(f"\n  单词：{display}")
        # 显示已猜字母
        alpha = "abcdefghijklmnopqrstuvwxyz"
        letter_line = " ".join(c.upper() if c in guessed else "·" for c in alpha)
        print(f"  字母：{letter_line}")

    def _record_win(self) -> None:
        self.wins += 1
        self.streak += 1
        if self.streak > self.best_streak:
            self.best_streak = self.streak

    def _record_loss(self) -> None:
        self.losses += 1
        self.streak = 0

    def show_stats(self) -> None:
        """展示游戏统计。"""
        total = self.wins + self.losses
        win_rate = (self.wins / total * 100) if total > 0 else 0
        print(f"\n  ═══ 游戏统计 ═══")
        print(f"  胜：{self.wins}  负：{self.losses}  胜率：{win_rate:.1f}%")
        print(f"  当前连胜：{self.streak}  最高连胜：{self.best_streak}")
        print()


# ── 主菜单 ────────────────────────────────────────────────


def print_menu() -> None:
    print("=" * 45)
    print("  终端小游戏 - 猜词（Hangman）")
    print("=" * 45)
    print("  1. 简单模式（3-5字母）")
    print("  2. 中等模式（6-7字母）")
    print("  3. 困难模式（8-10字母）")
    print("  4. 查看统计")
    print("  q. 退出")
    print("-" * 45)


def main() -> None:
    game = GuessWordGame()

    while True:
        print_menu()
        choice = input("  请选择: ").strip()

        if choice == "q":
            print("  再见！")
            break

        elif choice == "1":
            game.play("easy")
        elif choice == "2":
            game.play("medium")
        elif choice == "3":
            game.play("hard")
        elif choice == "4":
            game.show_stats()
        else:
            print("  无效选择，请重新输入")


if __name__ == "__main__":
    main()
