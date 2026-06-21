"""
纯 Python 实现的质数判断器（CLI）
支持：单数判断、范围查询、质因数分解、交互式 REPL
"""

import math
import sys


# ── 核心算法 ────────────────────────────────────────────────
def is_prime(n: int) -> bool:
    """判断一个整数是否为质数"""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    # 6k±1 优化
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def prime_range(start: int, end: int) -> list[int]:
    """返回 [start, end] 范围内的所有质数"""
    return [n for n in range(max(2, start), end + 1) if is_prime(n)]


def prime_factors(n: int) -> list[int]:
    """对整数 n 进行质因数分解，返回质因数列表"""
    if n < 2:
        return []
    factors: list[int] = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors


def next_prime(n: int) -> int:
    """返回大于 n 的下一个质数"""
    candidate = n + 1
    while not is_prime(candidate):
        candidate += 1
    return candidate


def count_primes(n: int) -> int:
    """返回小于等于 n 的质数个数"""
    return sum(1 for i in range(2, n + 1) if is_prime(i))


# ── 格式化输出 ──────────────────────────────────────────────
def fmt_factors(factors: list[int]) -> str:
    """将质因数列表格式化为乘法表达式"""
    if not factors:
        return "（无质因数）"
    # 合并相同因数
    from collections import Counter

    counts = Counter(factors)
    parts = [f"{p}^{c}" if c > 1 else str(p) for p, c in sorted(counts.items())]
    return " × ".join(parts)


# ── 交互式 REPL ────────────────────────────────────────────
def repl() -> None:
    print("=" * 50)
    print("  纯 Python 质数判断器 (CLI)")
    print("  输入数字判断质数，或使用以下命令：")
    print("  range <a> <b>  - 查询范围内质数")
    print("  factor <n>      - 质因数分解")
    print("  next <n>        - 下一个质数")
    print("  count <n>       - 统计 ≤n 的质数个数")
    print("  q               - 退出")
    print("=" * 50)

    while True:
        try:
            line = input("\n>>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not line:
            continue

        parts = line.split()

        if parts[0].lower() == "q":
            print("再见！")
            break

        # ── 范围查询 ──
        if parts[0].lower() == "range" and len(parts) >= 3:
            try:
                a, b = int(parts[1]), int(parts[2])
                primes = prime_range(a, b)
                if primes:
                    # 每行最多 10 个
                    for i in range(0, len(primes), 10):
                        chunk = primes[i : i + 10]
                        print("  " + "  ".join(f"{p:<8}" for p in chunk))
                    print(f"  共 {len(primes)} 个质数")
                else:
                    print(f"  [{a}, {b}] 范围内无质数")
            except ValueError:
                print("  错误：请输入有效整数，如 range 1 100")
            continue

        # ── 质因数分解 ──
        if parts[0].lower() == "factor" and len(parts) >= 2:
            try:
                n = int(parts[1])
                factors = prime_factors(n)
                print(f"  {n} = {fmt_factors(factors)}")
            except ValueError:
                print("  错误：请输入有效整数，如 factor 60")
            continue

        # ── 下一个质数 ──
        if parts[0].lower() == "next" and len(parts) >= 2:
            try:
                n = int(parts[1])
                np = next_prime(n)
                print(f"  大于 {n} 的下一个质数是 {np}")
            except ValueError:
                print("  错误：请输入有效整数，如 next 10")
            continue

        # ── 统计质数个数 ──
        if parts[0].lower() == "count" and len(parts) >= 2:
            try:
                n = int(parts[1])
                c = count_primes(n)
                print(f"  ≤ {n} 的质数共有 {c} 个")
            except ValueError:
                print("  错误：请输入有效整数，如 count 100")
            continue

        # ── 单数判断 ──
        try:
            n = int(parts[0])
            if is_prime(n):
                print(f"  {n} 是质数 ✓")
            else:
                factors = prime_factors(n)
                print(f"  {n} 不是质数 ✗")
                if factors and len(factors) > 1:
                    print(f"  {n} = {fmt_factors(factors)}")
        except ValueError:
            print("  错误：请输入有效整数或命令，输入 q 退出")


# ── 命令行入口 ──────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        try:
            n = int(arg)
            if is_prime(n):
                print(f"{n} 是质数")
            else:
                print(f"{n} 不是质数")
                factors = prime_factors(n)
                if factors:
                    print(f"{n} = {fmt_factors(factors)}")
        except ValueError:
            print(f"错误：'{arg}' 不是有效整数", file=sys.stderr)
            sys.exit(1)
    else:
        repl()
