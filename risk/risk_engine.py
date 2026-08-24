"""Fail-closed portfolio risk gate for paper/live execution."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class RiskLimits:
    max_daily_loss_pct: Decimal = Decimal("0.02")
    max_trade_notional_pct: Decimal = Decimal("0.01")
    max_asset_exposure_pct: Decimal = Decimal("0.10")
    max_venue_exposure_pct: Decimal = Decimal("0.40")
    max_total_exposure_pct: Decimal = Decimal("0.80")
    max_concurrent_trades: int = 5

@dataclass(frozen=True)
class PortfolioState:
    equity: Decimal
    day_start_equity: Decimal
    total_exposure: Decimal = Decimal(0)
    asset_exposure: Decimal = Decimal(0)
    venue_exposure: Decimal = Decimal(0)
    concurrent_trades: int = 0
    kill_switch: bool = False

@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    reason: str

class RiskEngine:
    def __init__(self, limits: RiskLimits | None = None) -> None:
        self.limits = limits or RiskLimits()

    def check(self, state: PortfolioState, trade_notional: Decimal) -> RiskDecision:
        if state.kill_switch:
            return RiskDecision(False, "kill_switch")
        if state.equity <= 0 or state.day_start_equity <= 0 or trade_notional <= 0:
            return RiskDecision(False, "invalid_portfolio_or_trade")
        daily_loss = max(Decimal(0), (state.day_start_equity - state.equity) / state.day_start_equity)
        if daily_loss >= self.limits.max_daily_loss_pct:
            return RiskDecision(False, "daily_loss_limit")
        if trade_notional / state.equity > self.limits.max_trade_notional_pct:
            return RiskDecision(False, "trade_notional_limit")
        if (state.asset_exposure + trade_notional) / state.equity > self.limits.max_asset_exposure_pct:
            return RiskDecision(False, "asset_exposure_limit")
        if (state.venue_exposure + trade_notional) / state.equity > self.limits.max_venue_exposure_pct:
            return RiskDecision(False, "venue_exposure_limit")
        if (state.total_exposure + trade_notional) / state.equity > self.limits.max_total_exposure_pct:
            return RiskDecision(False, "total_exposure_limit")
        if state.concurrent_trades >= self.limits.max_concurrent_trades:
            return RiskDecision(False, "concurrent_trade_limit")
        return RiskDecision(True, "approved")
