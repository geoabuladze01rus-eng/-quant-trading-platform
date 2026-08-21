"""Fail-safe controller for two-leg arbitrage execution.
It never assumes atomicity: one-leg fills become explicit hedge obligations.
"""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

class LegState(str, Enum): PENDING="PENDING"; PARTIAL="PARTIAL"; FILLED="FILLED"; FAILED="FAILED"; HEDGING="HEDGING"; HEDGED="HEDGED"
@dataclass(frozen=True)
class LegFill:
    filled: Decimal
    average_price: Decimal
    state: LegState
@dataclass(frozen=True)
class HedgeDecision:
    action: str
    quantity: Decimal
    reason: str

class TwoLegController:
    def __init__(self,max_unhedged_ms=500):
        if max_unhedged_ms<0: raise ValueError("max_unhedged_ms must be non-negative")
        self.max_unhedged_ms=max_unhedged_ms
    def reconcile(self,buy: LegFill,sell: LegFill,elapsed_ms: int)->HedgeDecision:
        imbalance=buy.filled-sell.filled
        if imbalance==0 and buy.state==LegState.FILLED and sell.state==LegState.FILLED:
            return HedgeDecision("COMPLETE",Decimal("0"),"both_legs_filled")
        if elapsed_ms>=self.max_unhedged_ms or buy.state==LegState.FAILED or sell.state==LegState.FAILED:
            if imbalance>0: return HedgeDecision("HEDGE_SELL",imbalance,"unhedged_buy_exposure")
            if imbalance<0: return HedgeDecision("HEDGE_BUY",-imbalance,"unhedged_sell_exposure")
        if imbalance>0: return HedgeDecision("WAIT_OR_CANCEL_SELL",imbalance,"temporary_buy_overfill")
        if imbalance<0: return HedgeDecision("WAIT_OR_CANCEL_BUY",-imbalance,"temporary_sell_overfill")
        return HedgeDecision("WAIT",Decimal("0"),"legs_not_yet_filled")
