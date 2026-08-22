"""Residual hedge planner for incomplete multi-leg arbitrage executions."""
from dataclasses import dataclass
from decimal import Decimal
@dataclass(frozen=True)
class ResidualExposure:
    symbol:str; side:str; quantity:Decimal; max_notional:Decimal
@dataclass(frozen=True)
class HedgePlan:
    symbol:str; side:str; quantity:Decimal; urgency:str; reason:str
class ResidualHedgePlanner:
    def plan(self,exposure:ResidualExposure,mark_price:Decimal,max_slippage_bps:Decimal=Decimal("20"))->HedgePlan:
        qty=Decimal(str(exposure.quantity)); px=Decimal(str(mark_price))
        if qty<=0 or px<=0:return HedgePlan(exposure.symbol,"NONE",Decimal(0),"NONE","no_residual")
        if qty*px>Decimal(str(exposure.max_notional)):return HedgePlan(exposure.symbol,"REDUCE",min(qty,Decimal(str(exposure.max_notional))/px),"IMMEDIATE","notional_cap")
        hedge_side="SELL" if exposure.side.upper()=="LONG" else "BUY"
        urgency="IMMEDIATE" if qty*px>=Decimal(str(exposure.max_notional))*Decimal("0.5") else "NORMAL"
        return HedgePlan(exposure.symbol,hedge_side,qty,urgency,"residual_exposure")
