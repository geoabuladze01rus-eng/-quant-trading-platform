"""Backtest result metrics."""
from dataclasses import dataclass
from decimal import Decimal
from math import sqrt

@dataclass(frozen=True)
class BacktestReport:
    final_equity: Decimal
    total_return: Decimal
    total_fees: Decimal
    trades: int
    max_drawdown: Decimal
    sharpe: Decimal
    sortino: Decimal

def report(starting_cash: Decimal, ending_cash: Decimal, pnl: list[Decimal], fees: Decimal) -> BacktestReport:
    equity = starting_cash
    peak = equity
    max_dd = Decimal("0")
    returns: list[float] = []
    for value in pnl:
        previous = equity
        equity += value
        if previous > 0:
            returns.append(float(value / previous))
        peak = max(peak, equity)
        if peak > 0:
            max_dd = max(max_dd, (peak - equity) / peak)
    if len(returns) > 1:
        mean = sum(returns) / len(returns)
        variance = sum((x - mean) ** 2 for x in returns) / (len(returns) - 1)
        std = sqrt(variance)
        sharpe = Decimal(str(mean / std * sqrt(len(returns)))) if std else Decimal("0")
        downside = sqrt(sum(min(x, 0.0) ** 2 for x in returns) / len(returns))
        sortino = Decimal(str(mean / downside * sqrt(len(returns)))) if downside else Decimal("0")
    else:
        sharpe = sortino = Decimal("0")
    return BacktestReport(ending_cash, (ending_cash - starting_cash) / starting_cash, fees, len(pnl), max_dd, sharpe, sortino)
