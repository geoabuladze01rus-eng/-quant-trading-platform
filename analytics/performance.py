"""Trading performance and risk-adjusted analytics."""
from dataclasses import dataclass
from decimal import Decimal
from math import sqrt


@dataclass(frozen=True)
class PerformanceReport:
    total_pnl: Decimal
    total_return: Decimal
    win_rate: Decimal
    profit_factor: Decimal
    max_drawdown: Decimal
    sharpe: Decimal
    sortino: Decimal
    trades: int

class PerformanceAnalyzer:
    def analyze(self, returns: list[Decimal], initial_equity: Decimal) -> PerformanceReport:
        if initial_equity <= 0: raise ValueError("initial equity must be positive")
        if not returns: return PerformanceReport(*(Decimal(0),)*7, 0)
        equity = initial_equity; peak = equity; max_dd = Decimal(0); wins = 0; gross_profit = Decimal(0); gross_loss = Decimal(0)
        for r in returns:
            equity += r
            if r > 0: wins += 1; gross_profit += r
            elif r < 0: gross_loss += -r
            peak = max(peak, equity)
            if peak > 0: max_dd = max(max_dd, (peak - equity) / peak)
        mean = sum(returns, Decimal(0)) / Decimal(len(returns))
        variance = sum((r - mean) ** 2 for r in returns) / Decimal(len(returns))
        std = variance.sqrt() if variance > 0 else Decimal(0)
        downside_var = sum(min(r, Decimal(0)) ** 2 for r in returns) / Decimal(len(returns))
        downside_std = downside_var.sqrt() if downside_var > 0 else Decimal(0)
        factor = Decimal(str(sqrt(len(returns))))
        sharpe = mean / std * factor if std else Decimal(0)
        sortino = mean / downside_std * factor if downside_std else Decimal(0)
        pf = gross_profit / gross_loss if gross_loss else (Decimal(999999) if gross_profit else Decimal(0))
        return PerformanceReport(equity - initial_equity, (equity - initial_equity) / initial_equity, Decimal(wins) / Decimal(len(returns)), pf, max_dd, sharpe, sortino, len(returns))
