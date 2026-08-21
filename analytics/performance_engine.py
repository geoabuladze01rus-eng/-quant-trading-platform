"""Performance analytics for paper/live trading results."""
from dataclasses import dataclass
from decimal import Decimal
from math import sqrt

@dataclass(frozen=True)
class PerformanceReport:
    trades: int
    total_pnl: Decimal
    gross_profit: Decimal
    gross_loss: Decimal
    fees: Decimal
    win_rate: Decimal
    profit_factor: Decimal
    average_trade: Decimal
    max_drawdown: Decimal
    sharpe: Decimal
    sortino: Decimal

class PerformanceEngine:
    def report(self, pnls: list[Decimal], fees: Decimal = Decimal("0"), periods_per_year: int = 365) -> PerformanceReport:
        if not pnls:
            return PerformanceReport(0, Decimal("0"), Decimal("0"), Decimal("0"), fees, Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"))
        values = [Decimal(x) for x in pnls]
        total = sum(values, Decimal("0")) - fees
        profit = sum((x for x in values if x > 0), Decimal("0"))
        loss = -sum((x for x in values if x < 0), Decimal("0"))
        win_rate = Decimal(sum(x > 0 for x in values)) / Decimal(len(values))
        pf = profit / loss if loss else Decimal("Infinity")
        average = total / Decimal(len(values))
        equity = peak = Decimal("0")
        max_dd = Decimal("0")
        for x in values:
            equity += x
            peak = max(peak, equity)
            max_dd = max(max_dd, peak - equity)
        mean = sum(values, Decimal("0")) / Decimal(len(values))
        variance = sum((x - mean) ** 2 for x in values) / Decimal(len(values))
        std = variance.sqrt() if variance > 0 else Decimal("0")
        annualizer = Decimal(str(sqrt(periods_per_year)))
        sharpe = (mean / std) * annualizer if std else Decimal("0")
        downside_var = sum(min(x, Decimal("0")) ** 2 for x in values) / Decimal(len(values))
        downside_std = downside_var.sqrt() if downside_var > 0 else Decimal("0")
        sortino = (mean / downside_std) * annualizer if downside_std else Decimal("0")
        return PerformanceReport(len(values), total, profit, loss, fees, win_rate, pf, average, max_dd, sharpe, sortino)
