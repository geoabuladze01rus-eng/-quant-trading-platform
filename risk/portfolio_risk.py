"""Portfolio risk engine with hard limits and emergency kill switch."""
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class RiskLimits:
    max_trade_notional: Decimal
    max_asset_exposure: Decimal
    max_venue_exposure: Decimal
    max_portfolio_exposure: Decimal
    max_daily_loss: Decimal
    max_drawdown: Decimal

@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    reason: str
    max_notional: Decimal

class PortfolioRiskEngine:
    def __init__(self, limits: RiskLimits):
        self.limits = limits
        self.daily_pnl = Decimal("0")
        self.peak_equity = None
        self.kill_switch = False

    def update_equity(self, equity: Decimal) -> None:
        if equity < 0: raise ValueError("equity cannot be negative")
        if self.peak_equity is None or equity > self.peak_equity: self.peak_equity = equity

    def update_daily_pnl(self, pnl: Decimal) -> None:
        self.daily_pnl = pnl
        if pnl <= -self.limits.max_daily_loss: self.kill_switch = True

    def current_drawdown(self, equity: Decimal) -> Decimal:
        if self.peak_equity is None or self.peak_equity == 0: return Decimal("0")
        return max(Decimal("0"), (self.peak_equity - equity) / self.peak_equity)

    def evaluate(self, trade_notional: Decimal, asset_exposure: Decimal, venue_exposure: Decimal, portfolio_exposure: Decimal, equity: Decimal) -> RiskDecision:
        if trade_notional <= 0: return RiskDecision(False, "invalid_trade_notional", Decimal("0"))
        self.update_equity(equity)
        if self.kill_switch: return RiskDecision(False, "kill_switch", Decimal("0"))
        if self.current_drawdown(equity) >= self.limits.max_drawdown:
            self.kill_switch = True
            return RiskDecision(False, "max_drawdown", Decimal("0"))
        checks = [
            (trade_notional > self.limits.max_trade_notional, "max_trade_notional", self.limits.max_trade_notional),
            (asset_exposure + trade_notional > self.limits.max_asset_exposure, "max_asset_exposure", max(Decimal("0"), self.limits.max_asset_exposure - asset_exposure)),
            (venue_exposure + trade_notional > self.limits.max_venue_exposure, "max_venue_exposure", max(Decimal("0"), self.limits.max_venue_exposure - venue_exposure)),
            (portfolio_exposure + trade_notional > self.limits.max_portfolio_exposure, "max_portfolio_exposure", max(Decimal("0"), self.limits.max_portfolio_exposure - portfolio_exposure)),
        ]
        for failed, reason, maximum in checks:
            if failed: return RiskDecision(False, reason, maximum)
        return RiskDecision(True, "approved", self.limits.max_trade_notional)
