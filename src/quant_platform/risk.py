from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from .domain import OrderIntent
from .execution_group import ArbitrageExecutionGroup

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
        if self.portfolio_exposure_pct + order_pct > self.max_portfolio_exposure_pct:
            return RiskDecision(False, "portfolio exposure limit exceeded")
        return RiskDecision(True, "approved")

    def evaluate_group(self, group: ArbitrageExecutionGroup, portfolio_value: Decimal) -> RiskDecision:
        """Approve/reject both arbitrage legs atomically using combined notional."""
        if portfolio_value <= 0:
            return RiskDecision(False, "portfolio_value must be positive")
        if self.daily_pnl_pct <= -self.max_daily_loss_pct:
            return RiskDecision(False, "daily loss limit reached")
        group_pct = group.notional / portfolio_value * Decimal("100")
        if group_pct > self.max_position_pct:
            return RiskDecision(False, "arbitrage group size limit exceeded")
        if self.portfolio_exposure_pct + group_pct > self.max_portfolio_exposure_pct:
            return RiskDecision(False, "portfolio exposure limit exceeded")
        if group.expected_gross_edge <= 0:
            return RiskDecision(False, "non-positive gross edge")
        return RiskDecision(True, "approved")
