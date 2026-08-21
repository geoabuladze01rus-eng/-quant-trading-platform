"""Adaptive strategy manager with champion/challenger promotion gates."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

class StrategyState(str, Enum):
    ACTIVE = "ACTIVE"
    CHALLENGER = "CHALLENGER"
    QUARANTINE = "QUARANTINE"
    DISABLED = "DISABLED"

@dataclass(frozen=True)
class StrategyStats:
    name: str
    trades: int
    sharpe: Decimal
    max_drawdown: Decimal
    profit_factor: Decimal
    expectancy: Decimal

@dataclass(frozen=True)
class StrategyDecision:
    strategy: str
    state: StrategyState
    risk_multiplier: Decimal
    reason: str

class AdaptiveStrategyManager:
    def __init__(self, min_trades: int = 200, max_drawdown: Decimal = Decimal("0.10"), min_expectancy: Decimal = Decimal("0")):
        self.min_trades = min_trades
        self.max_drawdown = max_drawdown
        self.min_expectancy = min_expectancy

    def evaluate(self, stats: StrategyStats, challenger: StrategyStats | None = None) -> StrategyDecision:
        if stats.trades < self.min_trades:
            return StrategyDecision(stats.name, StrategyState.CHALLENGER, Decimal("0.25"), "insufficient_sample")
        if stats.max_drawdown > self.max_drawdown or stats.expectancy <= self.min_expectancy:
            return StrategyDecision(stats.name, StrategyState.QUARANTINE, Decimal("0"), "edge_degradation_or_drawdown")
        if challenger and challenger.trades >= self.min_trades and challenger.sharpe > stats.sharpe and challenger.expectancy > stats.expectancy:
            return StrategyDecision(challenger.name, StrategyState.CHALLENGER, Decimal("0.05"), "challenger_requires_canary")
        return StrategyDecision(stats.name, StrategyState.ACTIVE, Decimal("1"), "champion_healthy")
