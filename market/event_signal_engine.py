"""Event-driven signal fusion for news, macro events and immediate market reaction."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
class SignalAction(str,Enum): IGNORE="IGNORE"; REDUCE="REDUCE"; BLOCK="BLOCK"; ALERT="ALERT"
@dataclass(frozen=True)
class EventSignal:
    event_id:str; impact:Decimal; sentiment:Decimal; surprise:Decimal; confidence:Decimal; price_reaction_bps:Decimal
@dataclass(frozen=True)
class EventDecision:
    action:SignalAction; risk_multiplier:Decimal; score:Decimal; reason:str
class EventDrivenSignalEngine:
    def evaluate(self,s:EventSignal)->EventDecision:
        confidence=max(Decimal(0),min(Decimal(1),s.confidence)); impact=abs(s.impact); surprise=abs(s.surprise); reaction=abs(s.price_reaction_bps)
        score=confidence*(impact+surprise+reaction/Decimal(100))
        if impact>=Decimal("0.9") and confidence>=Decimal("0.7"): return EventDecision(SignalAction.BLOCK,Decimal("0"),score,"critical_event")
        if score>=Decimal("1.2"): return EventDecision(SignalAction.REDUCE,Decimal("0.25"),score,"strong_event_signal")
        if score>=Decimal("0.6"): return EventDecision(SignalAction.REDUCE,Decimal("0.50"),score,"moderate_event_signal")
        return EventDecision(SignalAction.IGNORE,Decimal("1"),score,"insufficient_signal")
