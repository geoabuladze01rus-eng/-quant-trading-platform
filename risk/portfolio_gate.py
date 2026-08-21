"""Portfolio-level safety gate. Fails closed on invalid risk state."""

from dataclasses import dataclass
from decimal import Decimal

from core.portfolio import Portfolio
from execution.router import OrderRequest


@dataclass(frozen=True)
class PortfolioRiskLimits:
    max_daily_loss: Decimal = Decimal("0.02")
    max_drawdown: Decimal = Decimal("0.10")
    max_gross_exposure: Decimal = Decimal("1.00")
    max_order_notional: Decimal = Decimal("0.05")


class PortfolioRiskGate:
    def __init__(self, portfolio: Portfolio, limits: PortfolioRiskLimits | None = None) -> None:
        self.portfolio = portfolio
        self.limits = limits or PortfolioRiskLimits()

    def approve(self, request: OrderRequest) -> bool:
        equity = self.portfolio.equity
        if equity <= 0:
            return False
        if self.portfolio.daily_loss >= self.limits.max_daily_loss:
            return False
        if self.portfolio.drawdown >= self.limits.max_drawdown:
            return False
        if request.quantity <= 0:
            return False
        if request.limit_price is None or request.limit_price <= 0:
            return False
        notional = abs(request.quantity * request.limit_price)
        if notional / equity > self.limits.max_order_notional:
            return False
        projected = (self.portfolio.gross_exposure + notional) / equity
        return projected <= self.limits.max_gross_exposure
