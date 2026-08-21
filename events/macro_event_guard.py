"""Risk-first guard for scheduled macro/news events."""
from dataclasses import dataclass
from enum import Enum
class EventImpact(str,Enum): LOW="LOW"; MEDIUM="MEDIUM"; HIGH="HIGH"; CRITICAL="CRITICAL"
@dataclass(frozen=True)
class MacroEvent: event_id:str; timestamp_ms:int; impact:EventImpact; title:str
@dataclass(frozen=True)
class EventGuardDecision: allow_new_trades:bool; position_multiplier:float; reason:str
class MacroEventGuard:
    def __init__(self,blackout_before_ms=300000,blackout_after_ms=300000): self.blackout_before_ms=blackout_before_ms; self.blackout_after_ms=blackout_after_ms
    def evaluate(self,now_ms,event):
        distance=now_ms-event.timestamp_ms; inside=-self.blackout_before_ms<=distance<=self.blackout_after_ms
        if not inside:return EventGuardDecision(True,1.0,"outside_event_window")
        if event.impact==EventImpact.CRITICAL:return EventGuardDecision(False,0.0,"critical_event_blackout")
        if event.impact==EventImpact.HIGH:return EventGuardDecision(False,0.25,"high_impact_event")
        if event.impact==EventImpact.MEDIUM:return EventGuardDecision(True,0.50,"medium_impact_reduced_size")
        return EventGuardDecision(True,0.75,"low_impact_reduced_size")
