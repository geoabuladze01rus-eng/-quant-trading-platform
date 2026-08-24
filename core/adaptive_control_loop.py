"""Closed-loop controller connecting strategy health and macro risk."""
from dataclasses import dataclass
from decimal import Decimal

from intelligence.adaptive_strategy_manager import (
    AdaptiveStrategyManager,
    StrategyDecision,
    StrategyStats,
)


@dataclass(frozen=True)
class MacroRisk:
    level: str
    multiplier: Decimal
    reason: str = ""

@dataclass(frozen=True)
class ControlDecision:
    strategy_decision: StrategyDecision
    final_risk_multiplier: Decimal
    allowed: bool
    reason: str

class AdaptiveControlLoop:
    def __init__(self, manager=None):
        self.manager = manager or AdaptiveStrategyManager()

    def evaluate(self, champion: StrategyStats, macro: MacroRisk, challenger: StrategyStats | None = None) -> ControlDecision:
        strategy = self.manager.evaluate(champion, challenger)
        final_multiplier = strategy.risk_multiplier * macro.multiplier
        allowed = strategy.state.value not in {"QUARANTINE", "DISABLED"} and macro.multiplier > 0 and final_multiplier > 0
        reason = strategy.reason if allowed else (macro.reason or strategy.reason)
        return ControlDecision(strategy, final_multiplier if allowed else Decimal(0), allowed, reason)
