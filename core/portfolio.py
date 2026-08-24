"""Portfolio state and risk metrics used by the execution gate."""

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Position:
    symbol: str
    quantity: Decimal = Decimal("0")
    mark_price: Decimal = Decimal("0")

    @property
    def market_value(self) -> Decimal:
        return self.quantity * self.mark_price


@dataclass
class Portfolio:
    starting_equity: Decimal
    cash: Decimal
    positions: dict[str, Position] = field(default_factory=dict)
    realized_pnl: Decimal = Decimal("0")
    peak_equity: Decimal | None = None
    day_start_equity: Decimal | None = None

    def __post_init__(self) -> None:
        if self.peak_equity is None:
            self.peak_equity = max(self.starting_equity, self.equity)
        if self.day_start_equity is None:
            self.day_start_equity = self.starting_equity

    @property
    def equity(self) -> Decimal:
        return self.cash + sum((p.market_value for p in self.positions.values()), Decimal("0"))

    @property
    def drawdown(self) -> Decimal:
        if not self.peak_equity or self.peak_equity <= 0:
            return Decimal("0")
        return (self.peak_equity - self.equity) / self.peak_equity

    @property
    def daily_loss(self) -> Decimal:
        if not self.day_start_equity or self.day_start_equity <= 0:
            return Decimal("0")
        return max(Decimal("0"), (self.day_start_equity - self.equity) / self.day_start_equity)

    @property
    def gross_exposure(self) -> Decimal:
        return sum((abs(p.market_value) for p in self.positions.values()), Decimal("0"))

    def mark(self, symbol: str, price: Decimal) -> None:
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol=symbol)
        self.positions[symbol].mark_price = price
        if self.equity > (self.peak_equity or Decimal("0")):
            self.peak_equity = self.equity
