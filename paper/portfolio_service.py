"""Paper portfolio service: marks positions and records fills."""

from dataclasses import dataclass
from decimal import Decimal

from core.portfolio import Portfolio
from paper.fill_engine import PaperFill


@dataclass(frozen=True)
class PortfolioSnapshot:
    equity: Decimal
    cash: Decimal
    gross_exposure: Decimal
    daily_loss: Decimal
    drawdown: Decimal


class PaperPortfolioService:
    def __init__(self, portfolio: Portfolio) -> None:
        self.portfolio = portfolio
        self.fills: list[PaperFill] = []

    def record_fill(self, fill: PaperFill) -> None:
        self.fills.append(fill)

    def mark(self, symbol: str, price: Decimal) -> PortfolioSnapshot:
        self.portfolio.mark(symbol, price)
        return self.snapshot()

    def snapshot(self) -> PortfolioSnapshot:
        return PortfolioSnapshot(
            equity=self.portfolio.equity,
            cash=self.portfolio.cash,
            gross_exposure=self.portfolio.gross_exposure,
            daily_loss=self.portfolio.daily_loss,
            drawdown=self.portfolio.drawdown,
        )
