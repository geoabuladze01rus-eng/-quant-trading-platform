"""Residual-exposure hedge planning with hard notional and slippage caps."""
from dataclasses import dataclass
from decimal import Decimal
@dataclass(frozen=True)
class HedgeDecision:
    action:str; residual_quantity:Decimal; reason:str
@dataclass(frozen=True)
class HedgePlan:
    action:str; quantity:Decimal; max_price:Decimal; required:bool; reason:str
class HedgeManager:
    def __init__(self,max_hedge_slippage_bps=Decimal("30"),max_hedge_notional=Decimal("0")):
        self.max_hedge_slippage_bps=Decimal(str(max_hedge_slippage_bps)); self.max_hedge_notional=Decimal(str(max_hedge_notional))
    def assess(self,buy_filled,sell_filled,target_quantity,hedge_slippage_bps):
        buy_filled=Decimal(str(buy_filled)); sell_filled=Decimal(str(sell_filled)); target_quantity=Decimal(str(target_quantity))
        if min(buy_filled,sell_filled)<0 or target_quantity<=0: raise ValueError("invalid quantities")
        residual=buy_filled-sell_filled
        if residual==0:return HedgeDecision("NONE",Decimal(0),"legs balanced")
        if abs(residual)>target_quantity:raise ValueError("residual exceeds target")
        if Decimal(str(hedge_slippage_bps))>self.max_hedge_slippage_bps:return HedgeDecision("KILL",abs(residual),"hedge slippage exceeds limit")
        return HedgeDecision("SELL_HEDGE" if residual>0 else "BUY_HEDGE",abs(residual),"residual exposure")
    def plan(self,venue,symbol,residual,reference_price,max_notional):
        r=Decimal(str(residual)); p=Decimal(str(reference_price)); cap=Decimal(str(max_notional))
        if r==0:return HedgePlan("NONE",Decimal(0),p,False,"balanced")
        if p<=0 or abs(r)*p>cap:return HedgePlan("KILL",abs(r),p,True,"hedge_notional_limit")
        side="SELL_HEDGE" if r>0 else "BUY_HEDGE"; limit=p*(Decimal(1)+self.max_hedge_slippage_bps/Decimal(10000)) if r<0 else p*(Decimal(1)-self.max_hedge_slippage_bps/Decimal(10000))
        return HedgePlan(side,abs(r),limit,True,"hedge_required")
