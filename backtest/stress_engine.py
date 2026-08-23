"""Deterministic stress scenarios for arbitrage backtests."""
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Callable, Iterable, Any
@dataclass(frozen=True)
class StressScenario:
    name:str
    price_shock_bps:Decimal=Decimal(0)
    liquidity_factor:Decimal=Decimal(1)
    latency_ms:int=0
    venue_down:str|None=None
    partial_fill_factor:Decimal=Decimal(1)
@dataclass(frozen=True)
class StressResult:
    scenario:str
    result:Any
    passed:bool
    reason:str
class StressEngine:
    def __init__(self,max_drawdown=Decimal("0.10"),min_equity=Decimal("0")):
        self.max_drawdown=Decimal(str(max_drawdown)); self.min_equity=Decimal(str(min_equity))
    def run(self,scenarios:Iterable[StressScenario],runner:Callable[[StressScenario],Any])->tuple[StressResult,...]:
        out=[]
        for s in scenarios:
            try:
                result=runner(s); dd=Decimal(str(getattr(result,"max_drawdown",0))); equity=Decimal(str(getattr(result,"final_equity",0)))
                passed=dd<=self.max_drawdown and equity>=self.min_equity
                out.append(StressResult(s.name,result,passed,"ok" if passed else "risk_threshold_breached"))
            except Exception as exc: out.append(StressResult(s.name,None,False,f"runner_error:{type(exc).__name__}"))
        return tuple(out)
