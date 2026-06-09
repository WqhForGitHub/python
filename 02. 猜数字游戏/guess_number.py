"""
猜数字游戏
系统随机生成一个 1-100 的整数，玩家通过输入猜测数字，
系统给出"大了"或"小了"的提示，直到猜中为止。
"""

import random


def get_difficulty():
    """选择难度"""
    print("\n请选择难度：")
    print("1. 简单 (1-50, 无限次机会)")
    print("2. 普通 (1-100, 10次机会)")
    print("3. 困难 (1-200, 7次机会)")

    while True:
        choice = input("请输入难度 (1/2/3，默认2): ").strip()
        if choice == "" or choice == "2":
            return 100, 10
        elif choice == "1":
            return 50, 999
        elif choice == "3":
            return 200, 7
        else:
            print("无效输入，请重新选择。")


def play_game():
    """主游戏逻辑"""
    print("=" * 40)
    print("       欢迎来到猜数字游戏！")
    print("=" * 40)

    while True:
        max_num, max_attempts = get_difficulty()
        secret = random.randint(1, max_num)
        attempts = 0

        print(f"\n我已经想好了一个 1 到 {max_num} 之间的数字，开始猜吧！")
        if max_attempts < 999:
            print(f"你有 {max_attempts} 次机会。")
        print('输入 "q" 退出游戏，输入 "h" 获取提示。\n')

        while attempts < max_attempts:
            guess_input = input(f"第 {attempts + 1} 次猜测: ").strip()

            # 退出游戏
            if guess_input.lower() == "q":
                print(f"\n游戏结束！答案是 {secret}。")
                break

            # 提示功能
            if guess_input.lower() == "h":
                mid = (1 + max_num) // 2
                if secret <= mid:
                    print(f"  💡 提示：数字在 1 到 {mid} 之间")
                else:
                    print(f"  💡 提示：数字在 {mid + 1} 到 {max_num} 之间")
                continue

            # 验证输入
            if not guess_input.isdigit():
                print("  请输入一个有效的数字！")
                continue

            guess = int(guess_input)
            if guess < 1 or guess > max_num:
                print(f"  请输入 1 到 {max_num} 之间的数字！")
                continue

            attempts += 1

            if guess < secret:
                remaining = max_attempts - attempts if max_attempts < 999 else "∞"
                print(f"  小了！剩余机会: {remaining}")
            elif guess > secret:
                remaining = max_attempts - attempts if max_attempts < 999 else "∞"
                print(f"  大了！剩余机会: {remaining}")
            else:
                print(f"\n🎉 恭喜你！{attempts} 次猜中了！")
                # 评价
                if attempts == 1:
                    print("  太厉害了，一次就猜中！")
                elif attempts <= 3:
                    print("  非常优秀！")
                elif attempts <= 6:
                    print("  表现不错！")
                else:
                    print("  终于猜中了！")
                break
        else:
            print(f"\n😢 很遗憾，机会用完了！答案是 {secret}。")

        # 是否再玩一次
        again = input("\n再来一局？(y/n，默认y): ").strip().lower()
        if again == "n":
            print("\n感谢游玩，再见！")
            break
        print()


if __name__ == "__main__":
    play_game()
