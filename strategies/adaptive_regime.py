"""Conservative market-regime classifier and bounded strategy profiles."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import ClassVar


class MarketRegime(str, Enum):
    NORMAL="NORMAL"; HIGH_VOLATILITY="HIGH_VOLATILITY"; LOW_LIQUIDITY="LOW_LIQUIDITY"; TRENDING="TRENDING"; STRESS="STRESS"

@dataclass(frozen=True)
class MarketSnapshot:
    volatility: Decimal
    liquidity_score: Decimal
    trend_score: Decimal
    spread_bps: Decimal

@dataclass(frozen=True)
class StrategyProfile:
    regime: MarketRegime
    min_edge_bps: Decimal
    max_position_multiplier: Decimal
    enabled: bool

class RegimeClassifier:
    def classify(self,s):
        if s.volatility<0 or s.liquidity_score<0 or s.spread_bps<0: raise ValueError("invalid market snapshot")
        if s.liquidity_score<Decimal("0.25") or s.spread_bps>Decimal(100): return MarketRegime.LOW_LIQUIDITY
        if s.volatility>Decimal("0.08"): return MarketRegime.STRESS
        if s.volatility>Decimal("0.04"): return MarketRegime.HIGH_VOLATILITY
        if abs(s.trend_score)>Decimal("0.70"): return MarketRegime.TRENDING
        return MarketRegime.NORMAL

class AdaptiveProfileSelector:
    PROFILES: ClassVar[dict[MarketRegime, StrategyProfile]] = {
        MarketRegime.NORMAL:StrategyProfile(MarketRegime.NORMAL,Decimal(15),Decimal("1.0"),True),
        MarketRegime.TRENDING:StrategyProfile(MarketRegime.TRENDING,Decimal(20),Decimal("0.8"),True),
        MarketRegime.HIGH_VOLATILITY:StrategyProfile(MarketRegime.HIGH_VOLATILITY,Decimal(30),Decimal("0.5"),True),
        MarketRegime.LOW_LIQUIDITY:StrategyProfile(MarketRegime.LOW_LIQUIDITY,Decimal(50),Decimal("0.25"),False),
        MarketRegime.STRESS:StrategyProfile(MarketRegime.STRESS,Decimal(75),Decimal("0.10"),False),
    }
    def select(self,regime): return self.PROFILES[regime]
