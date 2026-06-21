"""
纯 Python 实现的汇率换算器 - 手动数据版（CLI）
支持：多币种换算、添加/删除/修改汇率、汇率列表、交互式 REPL
"""

import json
import os
import sys

# ── 默认汇率数据（基准：1 USD）──────────────────────────────
DEFAULT_RATES: dict[str, float] = {
    "USD": 1.0,  # 美元
    "CNY": 7.25,  # 人民币
    "EUR": 0.92,  # 欧元
    "GBP": 0.79,  # 英镑
    "JPY": 157.50,  # 日元
    "KRW": 1370.0,  # 韩元
    "HKD": 7.82,  # 港币
    "TWD": 32.50,  # 新台币
    "SGD": 1.35,  # 新加坡元
    "AUD": 1.55,  # 澳元
    "CAD": 1.37,  # 加元
    "CHF": 0.89,  # 瑞士法郎
    "THB": 36.20,  # 泰铢
    "MYR": 4.72,  # 马来西亚林吉特
    "INR": 83.50,  # 印度卢比
    "RUB": 92.00,  # 俄罗斯卢布
    "BRL": 5.05,  # 巴西雷亚尔
    "MXN": 17.15,  # 墨西哥比索
    "NZD": 1.70,  # 新西兰元
    "SEK": 10.85,  # 瑞典克朗
}

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rates.json")


# ── 数据持久化 ──────────────────────────────────────────────
def load_rates() -> dict[str, float]:
    """加载汇率数据，优先从文件读取"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return DEFAULT_RATES.copy()


def save_rates(rates: dict[str, float]) -> None:
    """保存汇率数据到文件"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(rates, f, indent=2, ensure_ascii=False)


# ── 核心计算 ────────────────────────────────────────────────
def convert(
    amount: float, from_currency: str, to_currency: str, rates: dict[str, float]
) -> float:
    """货币换算：通过 USD 基准进行交叉换算"""
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    if from_currency not in rates:
        raise ValueError(f"未知货币：{from_currency}")
    if to_currency not in rates:
        raise ValueError(f"未知货币：{to_currency}")

    # 先转为 USD，再转为目标货币
    usd_amount = amount / rates[from_currency]
    return usd_amount * rates[to_currency]


def cross_rate(from_currency: str, to_currency: str, rates: dict[str, float]) -> float:
    """计算交叉汇率"""
    return convert(1, from_currency, to_currency, rates)


# ── 交互式 REPL ────────────────────────────────────────────
def repl() -> None:
    rates = load_rates()

    print("=" * 54)
    print("  纯 Python 汇率换算器（手动数据）")
    print("  输入：金额 源币种 目标币种")
    print("  示例：100 USD CNY")
    print("  命令：")
    print("  list            - 列出所有汇率")
    print("  set <币种> <汇率> - 设置汇率(对USD)")
    print("  del <币种>      - 删除币种")
    print("  rate <A> <B>    - 查看交叉汇率")
    print("  reset           - 恢复默认汇率")
    print("  save            - 保存当前汇率")
    print("  q               - 退出")
    print("=" * 54)

    while True:
        try:
            line = input("\n>>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not line:
            continue

        parts = line.split()
        cmd = parts[0]

        if cmd.lower() == "q":
            print("再见！")
            break

        # ── 列出汇率 ──
        if cmd.lower() == "list":
            print(f"\n  {'币种':<6s} {'汇率(对1USD)':<16s} {'≈CNY'}")
            print("  " + "─" * 44)
            for currency in sorted(rates.keys()):
                rate = rates[currency]
                cny_equiv = rate / rates.get("CNY", 1) if "CNY" in rates else 0
                cny_str = f"{cny_equiv:.4f}" if currency != "CNY" else "-"
                print(f"  {currency:<6s} {rate:<16.4f} {cny_str}")
            print(f"\n  共 {len(rates)} 种货币")
            continue

        # ── 设置汇率 ──
        if cmd.lower() == "set" and len(parts) >= 3:
            try:
                currency = parts[1].upper()
                rate = float(parts[2])
                if rate <= 0:
                    print("  错误：汇率必须大于 0")
                    continue
                rates[currency] = rate
                print(f"  已设置 1 USD = {rate} {currency}")
            except ValueError:
                print("  错误：汇率必须是数字")
            continue

        # ── 删除币种 ──
        if cmd.lower() == "del" and len(parts) >= 2:
            currency = parts[1].upper()
            if currency in rates:
                if currency == "USD":
                    print("  错误：不能删除基准货币 USD")
                    continue
                del rates[currency]
                print(f"  已删除 {currency}")
            else:
                print(f"  未知币种：{currency}")
            continue

        # ── 交叉汇率 ──
        if cmd.lower() == "rate" and len(parts) >= 3:
            try:
                a, b = parts[1].upper(), parts[2].upper()
                cr = cross_rate(a, b, rates)
                print(f"  1 {a} = {cr:.6g} {b}")
                # 反向
                cr_rev = cross_rate(b, a, rates)
                print(f"  1 {b} = {cr_rev:.6g} {a}")
            except ValueError as e:
                print(f"  错误：{e}")
            continue

        # ── 恢复默认 ──
        if cmd.lower() == "reset":
            rates = DEFAULT_RATES.copy()
            print("  已恢复默认汇率")
            continue

        # ── 保存 ──
        if cmd.lower() == "save":
            save_rates(rates)
            print("  汇率已保存到文件")
            continue

        # ── 换算 ──
        if len(parts) >= 3:
            try:
                amount = float(parts[0])
                from_c = parts[1].upper()
                to_c = parts[2].upper()
                result = convert(amount, from_c, to_c, rates)

                # 格式化
                if abs(result) > 100:
                    result_str = f"{result:,.2f}"
                else:
                    result_str = f"{result:.4f}"

                print(f"  {amount:,.2f} {from_c} = {result_str} {to_c}")
            except ValueError as e:
                print(f"  错误：{e}")
            continue

        print("  用法：<金额> <源币种> <目标币种>，如 100 USD CNY")
        print("  输入 list 查看所有币种")


# ── 命令行入口 ──────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) >= 4:
        try:
            amount = float(sys.argv[1])
            from_c = sys.argv[2].upper()
            to_c = sys.argv[3].upper()
            rates = load_rates()
            result = convert(amount, from_c, to_c, rates)
            print(f"{amount:,.2f} {from_c} = {result:,.4f} {to_c}")
        except ValueError as e:
            print(f"错误：{e}", file=sys.stderr)
            sys.exit(1)
    else:
        repl()
