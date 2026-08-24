"""Explainable market-regime strategy router."""
from dataclasses import dataclass
from decimal import Decimal

from intelligence.market_regime import MarketRegime


@dataclass(frozen=True)
class StrategyPolicy:
    allowed: bool
    strategy: str
    risk_multiplier: Decimal
    reason: str

class StrategyRouter:
    def route(self, regime: MarketRegime) -> StrategyPolicy:
        if regime == MarketRegime.PANIC:
            return StrategyPolicy(False, "DEFENSIVE", Decimal(0), "panic_protection")
        if regime == MarketRegime.LOW_LIQUIDITY:
            return StrategyPolicy(False, "DEFENSIVE", Decimal(0), "liquidity_protection")
        if regime == MarketRegime.HIGH_VOLATILITY:
            return StrategyPolicy(True, "VOLATILITY_ARBITRAGE", Decimal("0.50"), "reduced_size_in_high_volatility")
        if regime == MarketRegime.BULL:
            return StrategyPolicy(True, "TREND_ARBITRAGE", Decimal("1.00"), "bull_regime")
        if regime == MarketRegime.BEAR:
            return StrategyPolicy(True, "DEFENSIVE_ARBITRAGE", Decimal("0.50"), "bear_regime")
        if regime == MarketRegime.SIDEWAYS:
            return StrategyPolicy(True, "MEAN_REVERSION_ARBITRAGE", Decimal("0.75"), "sideways_regime")
        return StrategyPolicy(False, "DEFENSIVE", Decimal(0), "unknown_regime")
