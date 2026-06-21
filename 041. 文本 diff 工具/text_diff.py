"""
文本 diff 工具
功能：
    - 行级 diff（两个文本逐行对比，输出增加/删除/不变）
    - 基于 LCS（最长公共子序列）的算法实现，纯 Python，无第三方
    - 同时演示 difflib 风格的对比（基于自实现）
    - 支持忽略空白、忽略大小写
    - 提供文件 diff 接口
    - 支持彩色（ANSI）输出
"""

import os


def lcs_matrix(a: list, b: list) -> list:
    """构建 LCS DP 矩阵"""
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m):
        for j in range(n):
            if a[i] == b[j]:
                dp[i + 1][j + 1] = dp[i][j] + 1
            else:
                dp[i + 1][j + 1] = max(dp[i + 1][j], dp[i][j + 1])
    return dp


def diff_lines(a: list, b: list) -> list:
    """对两组行计算 diff，返回 [(op, text)] 列表

    op:  ' '  相同
         '-'  仅在 a 中（删除）
         '+'  仅在 b 中（新增）
    """
    dp = lcs_matrix(a, b)
    i, j = len(a), len(b)
    result = []
    while i > 0 and j > 0:
        if a[i - 1] == b[j - 1]:
            result.append((" ", a[i - 1]))
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            result.append(("-", a[i - 1]))
            i -= 1
        else:
            result.append(("+", b[j - 1]))
            j -= 1
    while i > 0:
        result.append(("-", a[i - 1]))
        i -= 1
    while j > 0:
        result.append(("+", b[j - 1]))
        j -= 1
    return list(reversed(result))


def normalize_lines(lines: list, ignore_case: bool, ignore_ws: bool) -> list:
    out = []
    for ln in lines:
        s = ln
        if ignore_ws:
            s = " ".join(s.split())
        if ignore_case:
            s = s.lower()
        out.append(s)
    return out


def diff_text(text_a: str, text_b: str,
              ignore_case: bool = False,
              ignore_ws: bool = False) -> list:
    a_lines = text_a.splitlines()
    b_lines = text_b.splitlines()
    if ignore_case or ignore_ws:
        na = normalize_lines(a_lines, ignore_case, ignore_ws)
        nb = normalize_lines(b_lines, ignore_case, ignore_ws)
        ops = diff_lines(na, nb)
        # 把内容映射回原始（用游标恢复）
        ai = bi = 0
        out = []
        for op, _ in ops:
            if op == " ":
                out.append((" ", a_lines[ai]))
                ai += 1
                bi += 1
            elif op == "-":
                out.append(("-", a_lines[ai]))
                ai += 1
            else:
                out.append(("+", b_lines[bi]))
                bi += 1
        return out
    return diff_lines(a_lines, b_lines)


def diff_files(path_a: str, path_b: str, **kw) -> list:
    with open(path_a, "r", encoding="utf-8") as f:
        a = f.read()
    with open(path_b, "r", encoding="utf-8") as f:
        b = f.read()
    return diff_text(a, b, **kw)


# -------- 格式化输出 --------

ANSI = {
    "+": "\033[92m",  # 绿
    "-": "\033[91m",  # 红
    " ": "",
    "RESET": "\033[0m",
}


def render(diffs: list, color: bool = False, line_no: bool = True) -> str:
    out = []
    a_no = b_no = 1
    for op, line in diffs:
        if op == " ":
            prefix = f"  {a_no:>4} {b_no:>4} | "
            a_no += 1
            b_no += 1
        elif op == "-":
            prefix = f"- {a_no:>4}      | "
            a_no += 1
        else:
            prefix = f"+      {b_no:>4} | "
            b_no += 1
        if not line_no:
            prefix = f"{op} | "
        if color:
            out.append(f"{ANSI[op]}{prefix}{line}{ANSI['RESET']}")
        else:
            out.append(f"{prefix}{line}")
    return "\n".join(out)


def stats(diffs: list) -> dict:
    add = sum(1 for op, _ in diffs if op == "+")
    rem = sum(1 for op, _ in diffs if op == "-")
    same = sum(1 for op, _ in diffs if op == " ")
    return {"added": add, "removed": rem, "unchanged": same,
            "total": len(diffs)}


# ==================== Demo ====================

if __name__ == "__main__":
    print("=" * 60)
    print("  文本 diff 工具 Demo")
    print("=" * 60)

    text_a = """\
def greet(name):
    print("Hello, " + name)

def add(a, b):
    return a + b

print("done")
"""

    text_b = """\
def greet(name):
    print(f"Hello, {name}!")

def add(a, b):
    return a + b

def sub(a, b):
    return a - b

print("DONE")
"""

    print("\n--- 1. 基本 diff ---")
    diffs = diff_text(text_a, text_b)
    print(render(diffs))

    print("\n--- 2. 统计 ---")
    s = stats(diffs)
    print(f"  +{s['added']}  -{s['removed']}  ={s['unchanged']}  共 {s['total']} 行")

    print("\n--- 3. 忽略大小写 + 忽略空白 ---")
    diffs2 = diff_text(text_a, text_b, ignore_case=True, ignore_ws=True)
    s2 = stats(diffs2)
    print(f"  +{s2['added']}  -{s2['removed']}  ={s2['unchanged']}")

    # 文件 diff 演示
    print("\n--- 4. 文件 diff 演示 ---")
    base = os.path.dirname(os.path.abspath(__file__))
    fa = os.path.join(base, "_a.txt")
    fb = os.path.join(base, "_b.txt")
    with open(fa, "w", encoding="utf-8") as f:
        f.write(text_a)
    with open(fb, "w", encoding="utf-8") as f:
        f.write(text_b)
    res = diff_files(fa, fb)
    print(render(res, line_no=False))

    # 清理
    for f in (fa, fb):
        if os.path.exists(f):
            os.remove(f)

    # ANSI 彩色（在支持 ANSI 的终端可见）
    print("\n--- 5. 彩色输出（ANSI，部分终端可见） ---")
    print(render(diffs[:8], color=True))

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
