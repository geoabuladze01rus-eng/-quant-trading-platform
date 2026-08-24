"""Unified decision pipeline: intelligence -> router -> risk."""
from dataclasses import dataclass
from decimal import Decimal

from intelligence.strategy_router import StrategyPolicy, StrategyRouter
from risk.risk_engine import PortfolioState, RiskDecision, RiskEngine


@dataclass(frozen=True)
class TradeIntent:
    symbol: str
    notional: Decimal
    venue: str
    strategy: str

@dataclass(frozen=True)
class TradingDecision:
    approved: bool
    policy: StrategyPolicy
    risk: RiskDecision
    intent: TradeIntent | None

class TradingCore:
    def __init__(self, router=None, risk=None):
        self.router = router or StrategyRouter()
        self.risk = risk or RiskEngine()

    def decide(self, regime, symbol: str, venue: str, notional: Decimal, portfolio: PortfolioState) -> TradingDecision:
        policy = self.router.route(regime)
        if not policy.allowed:
            return TradingDecision(False, policy, RiskDecision(False, policy.reason), None)
        adjusted = notional * policy.risk_multiplier
        risk_decision = self.risk.check(portfolio, adjusted)
        if not risk_decision.approved:
            return TradingDecision(False, policy, risk_decision, None)
        intent = TradeIntent(symbol, adjusted, venue, policy.strategy)
        return TradingDecision(True, policy, risk_decision, intent)
