"""News and macro event risk gate. Provider-agnostic: adapters normalize external feeds."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class EventImpact(str,Enum): LOW="LOW"; MEDIUM="MEDIUM"; HIGH="HIGH"; CRITICAL="CRITICAL"
@dataclass(frozen=True)
class MarketEvent:
    event_id:str; title:str; timestamp_ms:int; impact:EventImpact; surprise_score:Decimal=Decimal(0)
@dataclass(frozen=True)
class EventDecision:
    risk_multiplier:Decimal; block_new_entries:bool; reason:str
class NewsMacroRiskEngine:
    def __init__(self,blackout_before_ms=120000,blackout_after_ms=180000): self.before=blackout_before_ms; self.after=blackout_after_ms
    def evaluate(self,now_ms:int,events:list[MarketEvent])->EventDecision:
        multiplier=Decimal(1); block=False; reasons=[]
        for e in events:
            dt=now_ms-e.timestamp_ms
            if e.impact==EventImpact.CRITICAL and -self.before<=dt<=self.after:return EventDecision(Decimal(0),True,"critical_macro_event")
            if e.impact==EventImpact.HIGH and -self.before<=dt<=self.after: multiplier=min(multiplier,Decimal("0.25")); block=True; reasons.append("high_impact_event")
            elif e.impact==EventImpact.MEDIUM and -self.before<=dt<=self.after: multiplier=min(multiplier,Decimal("0.50")); reasons.append("medium_impact_event")
        return EventDecision(multiplier,block,"|".join(reasons) if reasons else "normal")
