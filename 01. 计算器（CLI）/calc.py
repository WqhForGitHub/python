"""
纯 Python 实现的计算器（CLI）
支持：加、减、乘、除、取模、幂运算、括号、历史记录
"""

import operator
import re
import sys

# ── 运算符定义 ──────────────────────────────────────────────
OPS = {
    "+": (1, operator.add),
    "-": (1, operator.sub),
    "*": (2, operator.mul),
    "/": (2, operator.truediv),
    "%": (2, operator.mod),
    "^": (3, operator.pow),
}

# ── 词法分析 ────────────────────────────────────────────────
TOKEN_PATTERN = re.compile(
    r"\d+(?:\.\d+)?"  # 数字（整数 / 小数）
    r"|[\+\-\*/\^%()]"  # 运算符与括号
)


def tokenize(expr: str) -> list[str]:
    """将表达式字符串拆分为 token 列表，同时处理一元负号"""
    raw = TOKEN_PATTERN.findall(expr.replace(" ", ""))
    tokens: list[str] = []
    for i, tok in enumerate(raw):
        if tok == "-":
            # 判断是否为一元负号：在开头或左括号 / 运算符之后
            if i == 0 or raw[i - 1] in "(*+-/^%":
                tokens.extend(["0", "-"])  # 转为 0 - ...
                continue
        tokens.append(tok)
    return tokens


# ── 中缀 → 后缀（Shunting-yard）───────────────────────────
def shunting_yard(tokens: list[str]) -> list[str]:
    """Dijkstra Shunting-yard 算法，中缀表达式转后缀"""
    output: list[str] = []
    stack: list[str] = []

    for tok in tokens:
        if re.match(r"\d", tok):  # 数字
            output.append(tok)
        elif tok in OPS:  # 运算符
            while stack and stack[-1] in OPS and OPS[stack[-1]][0] >= OPS[tok][0]:
                output.append(stack.pop())
            stack.append(tok)
        elif tok == "(":  # 左括号
            stack.append(tok)
        elif tok == ")":  # 右括号
            while stack and stack[-1] != "(":
                output.append(stack.pop())
            stack.pop()  # 弹出 "("

    while stack:
        output.append(stack.pop())

    return output


# ── 后缀表达式求值 ──────────────────────────────────────────
def eval_postfix(postfix: list[str]) -> float:
    """对后缀表达式求值"""
    stack: list[float] = []
    for tok in postfix:
        if re.match(r"\d", tok):
            stack.append(float(tok))
        elif tok in OPS:
            b = stack.pop()
            a = stack.pop()
            result = OPS[tok][1](a, b)
            stack.append(result)
    return stack[0]


# ── 公开接口 ────────────────────────────────────────────────
def calculate(expr: str) -> float:
    """计算数学表达式字符串，返回结果"""
    tokens = tokenize(expr)
    if not tokens:
        raise ValueError("表达式为空")
    postfix = shunting_yard(tokens)
    return eval_postfix(postfix)


# ── 格式化输出 ──────────────────────────────────────────────
def fmt(value: float) -> str:
    """智能格式化：整数不带小数点，浮点数保留合理精度"""
    if value == int(value) and abs(value) < 1e15:
        return str(int(value))
    return f"{value:.10g}"


# ── 交互式 REPL ────────────────────────────────────────────
def repl() -> None:
    history: list[tuple[str, str]] = []

    print("=" * 48)
    print("  纯 Python 计算器 (CLI)")
    print("  输入表达式计算，输入 h 查看历史，q 退出")
    print("  支持: +  -  *  /  %  ^  ()")
    print("=" * 48)

    while True:
        try:
            line = input("\n>>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not line:
            continue
        if line.lower() == "q":
            print("再见！")
            break
        if line.lower() == "h":
            if not history:
                print("（暂无历史记录）")
            else:
                for i, (e, r) in enumerate(history, 1):
                    print(f"  {i:>3}. {e} = {r}")
            continue

        try:
            result = calculate(line)
            result_str = fmt(result)
            print(f"  = {result_str}")
            history.append((line, result_str))
        except ZeroDivisionError:
            print("  错误：除数不能为零")
        except (ValueError, IndexError):
            print("  错误：表达式格式不正确")
        except Exception as e:
            print(f"  错误：{e}")


# ── 命令行入口 ──────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 非交互模式：python calc.py "1+2*3"
        expr = " ".join(sys.argv[1:])
        try:
            print(fmt(calculate(expr)))
        except Exception as e:
            print(f"错误：{e}", file=sys.stderr)
            sys.exit(1)
    else:
        repl()
