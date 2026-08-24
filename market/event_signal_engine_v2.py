"""Event-driven signal fusion for news, macro events and immediate market response."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class SignalAction(str,Enum): IGNORE="IGNORE"; REDUCE="REDUCE"; PAUSE="PAUSE"; ALERT="ALERT"
@dataclass(frozen=True)
class EventSignal:
    event_id:str; impact:Decimal; sentiment:Decimal; confidence:Decimal; price_move_bps:Decimal; spread_change_bps:Decimal
@dataclass(frozen=True)
class EventDecision:
    action:SignalAction; risk_multiplier:Decimal; score:Decimal; reason:str
class EventDrivenSignalEngine:
    def evaluate(self,s:EventSignal)->EventDecision:
        impact=abs(Decimal(str(s.impact))); conf=Decimal(str(s.confidence)); move=abs(Decimal(str(s.price_move_bps))); spread=abs(Decimal(str(s.spread_change_bps))); score=impact*conf*(Decimal(1)+move/Decimal(100))
        if spread>=Decimal(25) or score>=Decimal("1.5"): return EventDecision(SignalAction.PAUSE,Decimal(0),score,"market_dislocation")
        if score>=Decimal("0.9"): return EventDecision(SignalAction.REDUCE,Decimal("0.25"),score,"high_confidence_event")
        if score>=Decimal("0.5"): return EventDecision(SignalAction.REDUCE,Decimal("0.50"),score,"event_risk")
        if conf>=Decimal("0.7"): return EventDecision(SignalAction.ALERT,Decimal(1),score,"monitor")
        return EventDecision(SignalAction.IGNORE,Decimal(1),score,"low_confidence")
