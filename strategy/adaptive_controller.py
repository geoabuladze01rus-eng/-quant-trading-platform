"""Bounded adaptive strategy parameters; learning may tune only inside hard risk limits."""
from dataclasses import dataclass
from decimal import Decimal
@dataclass(frozen=True)
class AdaptiveParams:
    min_edge_bps:Decimal; position_multiplier:Decimal; max_trade_frequency:int
class AdaptiveStrategyController:
    def __init__(self): self.bounds={"edge":(Decimal("3"),Decimal("20")),"size":(Decimal("0.25"),Decimal("1.0")),"freq":(1,60)}
    def parameters_for(self,regime:str)->AdaptiveParams:
        p={"QUIET":(Decimal("5"),Decimal("0.75"),30),"TREND":(Decimal("6"),Decimal("0.60"),20),"HIGH_VOL":(Decimal("8"),Decimal("0.40"),15),"STRESS":(Decimal("20"),Decimal("0.25"),5),"ILLIQUID":(Decimal("20"),Decimal("0.25"),2)}; e,s,f=p.get(regime,p["STRESS"]); return AdaptiveParams(e,s,f)
    def clamp(self,p:AdaptiveParams)->AdaptiveParams:
        lo,hi=self.bounds["edge"]; e=max(lo,min(hi,p.min_edge_bps)); lo,hi=self.bounds["size"]; s=max(lo,min(hi,p.position_multiplier)); f=max(self.bounds["freq"][0],min(self.bounds["freq"][1],p.max_trade_frequency)); return AdaptiveParams(e,s,f)
