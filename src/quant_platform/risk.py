from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .domain import OrderIntent


@dataclass(frozen=True, slots=True)
class RiskDecision:
    approved: bool
    reason: str


@dataclass(slots=True)
class RiskEngine:
    max_daily_loss_pct: Decimal = Decimal("2.0")
    max_position_pct: Decimal = Decimal("10.0")
    max_portfolio_exposure_pct: Decimal = Decimal("60.0")
    daily_pnl_pct: Decimal = Decimal("0")
    portfolio_exposure_pct: Decimal = Decimal("0")

    def evaluate(self, intent: OrderIntent, portfolio_value: Decimal) -> RiskDecision:
        if portfolio_value <= 0:
            return RiskDecision(False, "portfolio_value must be positive")

        if self.daily_pnl_pct <= -self.max_daily_loss_pct:
            return RiskDecision(False, "daily loss limit reached")

        order_notional = intent.quantity * (intent.limit_price or Decimal("0"))
        order_pct = order_notional / portfolio_value * Decimal("100")

        if order_pct > self.max_position_pct:
            return RiskDecision(False, "position size limit exceeded")

        projected_exposure = self.portfolio_exposure_pct + order_pct
        if projected_exposure > self.max_portfolio_exposure_pct:
            return RiskDecision(False, "portfolio exposure limit exceeded")

        return RiskDecision(True, "approved")
