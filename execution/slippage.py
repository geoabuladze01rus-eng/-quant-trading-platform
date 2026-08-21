"""Execution-cost model for paper trading."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal
Side = Literal["BUY", "SELL"]
@dataclass(frozen=True)
class ExecutionCostModel:
    fee_bps: Decimal = Decimal("10")
    slippage_bps: Decimal = Decimal("2")
    latency_bps: Decimal = Decimal("1")
    def execution_price(self, market_price: Decimal, side: Side) -> Decimal:
        if market_price <= 0:
            raise ValueError("market_price must be positive")
        impact = (self.slippage_bps + self.latency_bps) / Decimal("10000")
        return market_price * (Decimal("1") + impact) if side == "BUY" else market_price * (Decimal("1") - impact)
    def fee(self, quantity: Decimal, execution_price: Decimal) -> Decimal:
        if quantity <= 0 or execution_price <= 0:
            raise ValueError("quantity and execution_price must be positive")
        return quantity * execution_price * self.fee_bps / Decimal("10000")
    def total_cost_bps(self) -> Decimal:
        return self.fee_bps + self.slippage_bps + self.latency_bps
