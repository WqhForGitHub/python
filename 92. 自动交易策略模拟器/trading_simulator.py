"""
自动交易策略模拟器 - 纯 Python 实现
=====================================
功能：
- 生成/加载历史 K 线数据（OHLC）
- 实现常见技术指标：SMA、EMA、RSI、MACD、布林带
- 内置策略：双均线、RSI、布林带、MACD
- 回测引擎（含手续费、滑点、资金管理）
- 性能指标：总收益、年化、最大回撤、夏普比率、胜率
"""

import math
import random
from collections import namedtuple


Bar = namedtuple("Bar", ["t", "open", "high", "low", "close", "volume"])


# ---------- 数据生成 ----------
def random_walk_ohlc(n=300, start=100.0, vol=0.02, seed=42):
    """生成模拟价格序列"""
    random.seed(seed)
    bars = []
    price = start
    for i in range(n):
        change = random.gauss(0, vol)
        new_price = max(1.0, price * (1 + change))
        o = price
        c = new_price
        h = max(o, c) * (1 + abs(random.gauss(0, vol / 2)))
        l = min(o, c) * (1 - abs(random.gauss(0, vol / 2)))
        v = random.randint(1000, 10000)
        bars.append(Bar(i, o, h, l, c, v))
        price = new_price
    return bars


# ---------- 技术指标 ----------
def sma(values, n):
    out = [None] * len(values)
    s = 0.0
    for i, v in enumerate(values):
        s += v
        if i >= n:
            s -= values[i - n]
        if i >= n - 1:
            out[i] = s / n
    return out


def ema(values, n):
    out = [None] * len(values)
    if not values:
        return out
    k = 2 / (n + 1)
    out[0] = values[0]
    for i in range(1, len(values)):
        out[i] = values[i] * k + out[i - 1] * (1 - k)
    return out


def rsi(values, n=14):
    out = [None] * len(values)
    if len(values) < n + 1:
        return out
    gains = losses = 0.0
    for i in range(1, n + 1):
        ch = values[i] - values[i - 1]
        if ch > 0:
            gains += ch
        else:
            losses -= ch
    avg_g = gains / n
    avg_l = losses / n
    out[n] = 100 - 100 / (1 + (avg_g / avg_l if avg_l > 0 else 1e9))
    for i in range(n + 1, len(values)):
        ch = values[i] - values[i - 1]
        g = ch if ch > 0 else 0
        l = -ch if ch < 0 else 0
        avg_g = (avg_g * (n - 1) + g) / n
        avg_l = (avg_l * (n - 1) + l) / n
        out[i] = 100 - 100 / (1 + (avg_g / avg_l if avg_l > 0 else 1e9))
    return out


def macd(values, fast=12, slow=26, signal=9):
    ef = ema(values, fast)
    es = ema(values, slow)
    line = [a - b if a is not None and b is not None else None for a, b in zip(ef, es)]
    valid = [x for x in line if x is not None]
    sig_part = ema(valid, signal) if valid else []
    sig = [None] * (len(line) - len(sig_part)) + sig_part
    hist = [a - b if a is not None and b is not None else None for a, b in zip(line, sig)]
    return line, sig, hist


def bollinger(values, n=20, k=2.0):
    mid = sma(values, n)
    upper = [None] * len(values)
    lower = [None] * len(values)
    for i in range(n - 1, len(values)):
        window = values[i - n + 1:i + 1]
        m = mid[i]
        var = sum((x - m) ** 2 for x in window) / n
        std = math.sqrt(var)
        upper[i] = m + k * std
        lower[i] = m - k * std
    return upper, mid, lower


# ---------- 策略基类 ----------
class Strategy:
    def __init__(self, name="Strategy"):
        self.name = name

    def signals(self, bars):
        """返回与 bars 等长的信号列表：1=买入, -1=卖出, 0=持有"""
        raise NotImplementedError


class DoubleMAStrategy(Strategy):
    def __init__(self, fast=5, slow=20):
        super().__init__(f"双均线({fast}/{slow})")
        self.fast = fast
        self.slow = slow

    def signals(self, bars):
        closes = [b.close for b in bars]
        f = sma(closes, self.fast)
        s = sma(closes, self.slow)
        sig = [0] * len(bars)
        for i in range(1, len(bars)):
            if f[i] is None or s[i] is None or f[i - 1] is None or s[i - 1] is None:
                continue
            if f[i - 1] <= s[i - 1] and f[i] > s[i]:
                sig[i] = 1
            elif f[i - 1] >= s[i - 1] and f[i] < s[i]:
                sig[i] = -1
        return sig


class RSIStrategy(Strategy):
    def __init__(self, n=14, lower=30, upper=70):
        super().__init__(f"RSI({n},{lower}/{upper})")
        self.n = n
        self.lower = lower
        self.upper = upper

    def signals(self, bars):
        closes = [b.close for b in bars]
        r = rsi(closes, self.n)
        sig = [0] * len(bars)
        for i in range(1, len(bars)):
            if r[i] is None or r[i - 1] is None:
                continue
            if r[i - 1] < self.lower <= r[i]:
                sig[i] = 1
            elif r[i - 1] > self.upper >= r[i]:
                sig[i] = -1
        return sig


class BollingerStrategy(Strategy):
    def __init__(self, n=20, k=2.0):
        super().__init__(f"布林带({n},{k})")
        self.n = n
        self.k = k

    def signals(self, bars):
        closes = [b.close for b in bars]
        u, m, l = bollinger(closes, self.n, self.k)
        sig = [0] * len(bars)
        for i in range(1, len(bars)):
            if (l[i] is None or u[i] is None
                    or l[i - 1] is None or u[i - 1] is None):
                continue
            if closes[i - 1] > l[i - 1] and closes[i] <= l[i]:
                sig[i] = 1
            elif closes[i - 1] < u[i - 1] and closes[i] >= u[i]:
                sig[i] = -1
        return sig


# ---------- 回测引擎 ----------
class Backtester:
    def __init__(self, init_cash=100000.0, fee=0.0003, slippage=0.0005):
        self.init_cash = init_cash
        self.fee = fee
        self.slippage = slippage

    def run(self, bars, strategy):
        signals = strategy.signals(bars)
        cash = self.init_cash
        position = 0  # 持仓股数
        trades = []
        equity_curve = []

        for i, bar in enumerate(bars):
            sig = signals[i]
            price = bar.close
            if sig == 1 and position == 0:
                # 全仓买入
                buy_price = price * (1 + self.slippage)
                qty = int(cash // (buy_price * (1 + self.fee)))
                if qty > 0:
                    cost = qty * buy_price * (1 + self.fee)
                    cash -= cost
                    position = qty
                    trades.append(("BUY", i, buy_price, qty))
            elif sig == -1 and position > 0:
                sell_price = price * (1 - self.slippage)
                proceeds = position * sell_price * (1 - self.fee)
                trades.append(("SELL", i, sell_price, position, proceeds - trades[-1][3] * trades[-1][2]))
                cash += proceeds
                position = 0

            equity = cash + position * price
            equity_curve.append(equity)

        # 强平
        if position > 0:
            cash += position * bars[-1].close * (1 - self.fee - self.slippage)
            position = 0

        return self._stats(equity_curve, trades)

    def _stats(self, eq, trades):
        if not eq:
            return {}
        total_ret = (eq[-1] - self.init_cash) / self.init_cash
        # 最大回撤
        peak = eq[0]
        mdd = 0.0
        for v in eq:
            peak = max(peak, v)
            mdd = max(mdd, (peak - v) / peak)
        # 夏普
        rets = [(eq[i] - eq[i - 1]) / eq[i - 1] for i in range(1, len(eq)) if eq[i - 1] != 0]
        if rets:
            mean = sum(rets) / len(rets)
            var = sum((r - mean) ** 2 for r in rets) / len(rets)
            std = math.sqrt(var)
            sharpe = (mean / std * math.sqrt(252)) if std > 0 else 0
        else:
            sharpe = 0
        # 胜率
        wins = sum(1 for t in trades if t[0] == "SELL" and len(t) > 4 and t[4] > 0)
        sells = sum(1 for t in trades if t[0] == "SELL")
        winrate = wins / sells if sells else 0
        return {
            "final_equity": eq[-1],
            "total_return": total_ret,
            "max_drawdown": mdd,
            "sharpe": sharpe,
            "trades": len(trades),
            "win_rate": winrate,
            "equity_curve": eq,
        }


def demo():
    bars = random_walk_ohlc(n=400, start=100, vol=0.02, seed=2024)
    bt = Backtester(init_cash=100000)

    strategies = [
        DoubleMAStrategy(5, 20),
        RSIStrategy(14, 30, 70),
        BollingerStrategy(20, 2.0),
    ]

    print("=" * 60)
    print(f"{'策略':<20} {'收益':>8} {'最大回撤':>10} {'夏普':>8} {'交易':>6} {'胜率':>8}")
    print("-" * 60)
    for s in strategies:
        r = bt.run(bars, s)
        print(f"{s.name:<20} "
              f"{r['total_return']*100:>7.2f}% "
              f"{r['max_drawdown']*100:>9.2f}% "
              f"{r['sharpe']:>8.2f} "
              f"{r['trades']:>6} "
              f"{r['win_rate']*100:>7.2f}%")
    print("=" * 60)

    # 简单 ASCII 资金曲线
    r = bt.run(bars, DoubleMAStrategy(5, 20))
    eq = r["equity_curve"]
    print("\n资金曲线 (双均线策略):")
    plot_h = 12
    mn, mx = min(eq), max(eq)
    width = 60
    step = max(1, len(eq) // width)
    sampled = eq[::step][:width]
    for row in range(plot_h, -1, -1):
        threshold_v = mn + (mx - mn) * row / plot_h
        line = ""
        for v in sampled:
            line += "█" if v >= threshold_v else " "
        print(f"{threshold_v:>9.0f} |{line}")
    print(f"{'':>9}  {'-'*len(sampled)}")


if __name__ == "__main__":
    demo()
