"""
纯 Python 实现的阶乘计算器（CLI）
支持：阶乘计算、排列组合、双阶乘、交互式 REPL
"""

import sys


# ── 核心算法 ────────────────────────────────────────────────
def factorial(n: int) -> int:
    """计算 n!（n 的阶乘）"""
    if n < 0:
        raise ValueError("负数没有阶乘")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def double_factorial(n: int) -> int:
    """计算 n!!（双阶乘）"""
    if n < 0:
        raise ValueError("负数没有双阶乘")
    result = 1
    while n > 0:
        result *= n
        n -= 2
    return result


def permutation(n: int, k: int) -> int:
    """计算排列数 P(n, k) = n! / (n-k)!"""
    if n < 0 or k < 0 or k > n:
        raise ValueError("参数无效：需要 0 <= k <= n")
    result = 1
    for i in range(n, n - k, -1):
        result *= i
    return result


def combination(n: int, k: int) -> int:
    """计算组合数 C(n, k) = n! / (k! * (n-k)!)"""
    if n < 0 or k < 0 or k > n:
        raise ValueError("参数无效：需要 0 <= k <= n")
    k = min(k, n - k)  # 优化：C(n,k) = C(n,n-k)
    result = 1
    for i in range(k):
        result = result * (n - i) // (i + 1)
    return result


def stirling_approx(n: int) -> float:
    """Stirling 近似公式估算 n! ≈ √(2πn) · (n/e)^n"""
    import math

    if n < 1:
        return 1.0
    return math.sqrt(2 * math.pi * n) * (n / math.e) ** n


def factorial_digits(n: int) -> int:
    """计算 n! 的位数（不实际计算阶乘）"""
    if n <= 1:
        return 1
    import math

    # 利用 log10(n!) = Σ log10(k)
    return int(sum(math.log10(k) for k in range(2, n + 1))) + 1


# ── 格式化输出 ──────────────────────────────────────────────
def fmt_large(n: int, max_show: int = 50) -> str:
    """格式化大数：较短时完整显示，较长时截断并显示位数"""
    s = str(n)
    if len(s) <= max_show:
        return s
    return f"{s[:20]}...{s[-20:]}（共 {len(s)} 位）"


# ── 交互式 REPL ────────────────────────────────────────────
def repl() -> None:
    print("=" * 50)
    print("  纯 Python 阶乘计算器 (CLI)")
    print("  输入数字计算阶乘，或使用以下命令：")
    print("  P <n> <k>       - 排列数 P(n,k)")
    print("  C <n> <k>       - 组合数 C(n,k)")
    print("  df <n>          - 双阶乘 n!!")
    print("  approx <n>      - Stirling 近似")
    print("  digits <n>      - n! 的位数")
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

        # ── 排列数 ──
        if parts[0].upper() == "P" and len(parts) >= 3:
            try:
                n, k = int(parts[1]), int(parts[2])
                result = permutation(n, k)
                print(f"  P({n}, {k}) = {fmt_large(result)}")
            except ValueError as e:
                print(f"  错误：{e}")
            continue

        # ── 组合数 ──
        if parts[0].upper() == "C" and len(parts) >= 3:
            try:
                n, k = int(parts[1]), int(parts[2])
                result = combination(n, k)
                print(f"  C({n}, {k}) = {result}")
            except ValueError as e:
                print(f"  错误：{e}")
            continue

        # ── 双阶乘 ──
        if parts[0].lower() == "df" and len(parts) >= 2:
            try:
                n = int(parts[1])
                result = double_factorial(n)
                print(f"  {n}!! = {fmt_large(result)}")
            except ValueError as e:
                print(f"  错误：{e}")
            continue

        # ── Stirling 近似 ──
        if parts[0].lower() == "approx" and len(parts) >= 2:
            try:
                n = int(parts[1])
                approx = stirling_approx(n)
                exact = factorial(n)
                print(f"  Stirling 近似：{approx:.6e}")
                print(f"  精确值：        {float(exact):.6e}")
                if exact > 0:
                    err = abs(approx - exact) / exact * 100
                    print(f"  相对误差：      {err:.4f}%")
            except ValueError as e:
                print(f"  错误：{e}")
            continue

        # ── 位数 ──
        if parts[0].lower() == "digits" and len(parts) >= 2:
            try:
                n = int(parts[1])
                d = factorial_digits(n)
                print(f"  {n}! 共有 {d} 位")
            except ValueError as e:
                print(f"  错误：{e}")
            continue

        # ── 阶乘 ──
        try:
            n = int(parts[0])
            if n < 0:
                print("  错误：负数没有阶乘")
                continue
            result = factorial(n)
            print(f"  {n}! = {fmt_large(result)}")
            # 显示小阶乘的展开式
            if 1 <= n <= 10:
                expr = " × ".join(str(i) for i in range(1, n + 1))
                print(f"     = {expr}")
        except ValueError:
            print("  错误：请输入有效整数或命令，输入 q 退出")


# ── 命令行入口 ──────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        try:
            n = int(arg)
            result = factorial(n)
            print(f"{n}! = {fmt_large(result)}")
        except ValueError as e:
            print(f"错误：{e}", file=sys.stderr)
            sys.exit(1)
    else:
        repl()
