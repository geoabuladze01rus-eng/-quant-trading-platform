"""Calculates residual exposure after partial two-leg arbitrage fills."""
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class HedgeDecision:
    action: str
    residual_quantity: Decimal
    reason: str

class HedgeManager:
    def __init__(self, max_hedge_slippage_bps=Decimal("30")):
        self.max_hedge_slippage_bps = Decimal(str(max_hedge_slippage_bps))

    def assess(self, buy_filled, sell_filled, target_quantity, hedge_slippage_bps):
        buy_filled=Decimal(str(buy_filled)); sell_filled=Decimal(str(sell_filled)); target_quantity=Decimal(str(target_quantity))
        if min(buy_filled,sell_filled)<0 or target_quantity<=0: raise ValueError("invalid quantities")
        residual=buy_filled-sell_filled
        if residual==0: return HedgeDecision("NONE",Decimal("0"),"legs balanced")
        if abs(residual)>target_quantity: raise ValueError("residual exceeds target")
        if Decimal(str(hedge_slippage_bps))>self.max_hedge_slippage_bps: return HedgeDecision("KILL",abs(residual),"hedge slippage exceeds limit")
        return HedgeDecision("SELL_HEDGE" if residual>0 else "BUY_HEDGE",abs(residual),"residual exposure")
