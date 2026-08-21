"""Append-only trade journal and deterministic performance analytics."""
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from math import sqrt

@dataclass(frozen=True)
class TradeEvent:
    event_type: str
    timestamp: datetime
    strategy: str
    venue: str
    symbol: str
    side: str
    quantity: Decimal
    price: Decimal
    fee: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    latency_ms: float = 0.0

class TradeJournal:
    def __init__(self) -> None:
        self.events: list[TradeEvent] = []

    def append(self, event: TradeEvent) -> None:
        if event.timestamp.tzinfo is None:
            raise ValueError("trade event timestamp must be timezone-aware")
        self.events.append(event)

    def fills(self) -> list[TradeEvent]:
        return [e for e in self.events if e.event_type == "ORDER_FILLED"]

@dataclass(frozen=True)
class PerformanceReport:
    total_pnl: Decimal
    total_fees: Decimal
    trades: int
    win_rate: Decimal
    profit_factor: Decimal
    max_drawdown: Decimal
    sharpe: Decimal
    sortino: Decimal
    average_latency_ms: Decimal

def performance_report(events: list[TradeEvent], starting_equity: Decimal) -> PerformanceReport:
    fills = [e for e in events if e.event_type == "ORDER_FILLED"]
    pnl = [e.realized_pnl for e in fills]
    fees = sum((e.fee for e in fills), Decimal("0"))
    total = sum(pnl, Decimal("0")) - fees
    wins = [x for x in pnl if x > 0]
    losses = [-x for x in pnl if x < 0]
    win_rate = Decimal(len(wins)) / Decimal(len(pnl)) if pnl else Decimal("0")
    profit_factor = sum(wins, Decimal("0")) / sum(losses, Decimal("0")) if losses else Decimal("0")
    equity, peak, max_dd = starting_equity, starting_equity, Decimal("0")
    returns: list[float] = []
    for x in pnl:
        previous = equity
        equity += x
        if previous > 0:
            returns.append(float(x / previous))
        peak = max(peak, equity)
        if peak > 0:
            max_dd = max(max_dd, (peak - equity) / peak)
    if len(returns) > 1:
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
        std = sqrt(variance)
        sharpe = Decimal(str(mean / std * sqrt(len(returns)))) if std else Decimal("0")
        down = sqrt(sum(min(r, 0.0) ** 2 for r in returns) / len(returns))
        sortino = Decimal(str(mean / down * sqrt(len(returns)))) if down else Decimal("0")
    else:
        sharpe = sortino = Decimal("0")
    avg_latency = Decimal(str(sum(e.latency_ms for e in fills) / len(fills))) if fills else Decimal("0")
    return PerformanceReport(total, fees, len(fills), win_rate, profit_factor, max_dd, sharpe, sortino, avg_latency)

def now_utc() -> datetime:
    return datetime.now(timezone.utc)
