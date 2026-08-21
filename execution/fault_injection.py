"""Deterministic execution fault injection for stress testing. Never used by production adapters."""
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class ExecutionScenario:
    latency_ms: int = 0
    fill_ratio: Decimal = Decimal("1")
    fail_sell: bool = False
    fail_buy: bool = False
    slippage_bps: Decimal = Decimal("0")

class FaultInjector:
    def __init__(self, scenario=None):
        self.scenario = scenario or ExecutionScenario()
        if not 0 <= self.scenario.fill_ratio <= 1: raise ValueError("fill_ratio must be 0..1")
        if self.scenario.latency_ms < 0 or self.scenario.slippage_bps < 0: raise ValueError("invalid scenario")
    def effective_quantity(self, quantity): return Decimal(str(quantity)) * self.scenario.fill_ratio
    def adjusted_price(self, price, side):
        price=Decimal(str(price)); bps=self.scenario.slippage_bps/Decimal("10000")
        return price*(1+bps) if side == "BUY" else price*(1-bps)
    def should_fail(self, side): return self.scenario.fail_buy if side == "BUY" else self.scenario.fail_sell
