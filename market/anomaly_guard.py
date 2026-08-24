"""Anomaly and bad-quote guard for real-time arbitrage decisions."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class AnomalyResult:
    score:Decimal; stale:bool; crossed:bool; outlier:bool; allowed:bool; reason:str
class AnomalyGuard:
    def evaluate(self,bid:Decimal,ask:Decimal,reference:Decimal,age_ms:int,max_age_ms:int=1000,max_deviation_bps:int=50)->AnomalyResult:
        bid=Decimal(str(bid)); ask=Decimal(str(ask)); ref=Decimal(str(reference)); stale=age_ms>max_age_ms; crossed=bid>=ask
        deviation=abs(((bid+ask)/2-ref)/ref*Decimal(10000)) if ref>0 else Decimal(999999); outlier=deviation>Decimal(max_deviation_bps); score=min(Decimal(1),deviation/Decimal(max_deviation_bps)) if max_deviation_bps else Decimal(1)
        allowed=not(stale or crossed or outlier); reason="OK" if allowed else ",".join(x for x,y in (("STALE",stale),("CROSSED",crossed),("OUTLIER",outlier)) if y)
        return AnomalyResult(score,stale,crossed,outlier,allowed,reason)
