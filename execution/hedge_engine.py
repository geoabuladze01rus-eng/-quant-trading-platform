"""Residual-exposure hedge selector."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class HedgeCandidate:
    venue:str; instrument:str; liquidity_score:Decimal; latency_ms:int; fee_bps:Decimal; slippage_bps:Decimal; hedge_capacity:Decimal
@dataclass(frozen=True)
class HedgeDecision:
    venue:str; instrument:str; quantity:Decimal; score:Decimal; approved:bool; reason:str
class HedgeEngine:
    def select(self,residual_qty:Decimal,candidates:list[HedgeCandidate],max_slippage_bps:Decimal=Decimal(20))->HedgeDecision:
        qty=Decimal(str(residual_qty)); best=None
        for c in candidates:
            cap=Decimal(str(c.hedge_capacity)); slip=Decimal(str(c.slippage_bps)); liq=Decimal(str(c.liquidity_score))
            if cap<=0 or slip>max_slippage_bps or liq<=0: continue
            q=min(qty,cap); score=(slip+Decimal(str(c.fee_bps))+Decimal(c.latency_ms)/Decimal(100))/liq
            if best is None or score<best[0]: best=(score,c,q)
        if best is None:return HedgeDecision("","",Decimal(0),Decimal(0),False,"no_safe_hedge")
        score,c,q=best; return HedgeDecision(c.venue,c.instrument,q,score,True,"approved")
