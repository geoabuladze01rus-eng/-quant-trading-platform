"""Macro/news risk layer. It changes risk posture; it never places orders."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class NewsImpact(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME = "EXTREME"

@dataclass(frozen=True)
class MacroEvent:
    source: str
    event_id: str
    title: str
    timestamp_ms: int
    impact: NewsImpact
    surprise_score: Decimal = Decimal(0)
    confidence: Decimal = Decimal(0)

@dataclass(frozen=True)
class MacroRiskState:
    impact: NewsImpact
    risk_multiplier: Decimal
    halt_new_entries: bool
    reason: str

class MacroNewsGuard:
    def __init__(self, pre_event_seconds: int = 60, post_event_seconds: int = 120):
        self.pre_event_seconds = pre_event_seconds
        self.post_event_seconds = post_event_seconds

    def evaluate(self, event: MacroEvent, now_ms: int) -> MacroRiskState:
        distance = abs(now_ms - event.timestamp_ms) / 1000
        if event.impact == NewsImpact.EXTREME or event.surprise_score >= Decimal(3):
            return MacroRiskState(event.impact, Decimal(0), True, "extreme_macro_event")
        if distance <= self.pre_event_seconds or distance <= self.post_event_seconds:
            if event.impact == NewsImpact.HIGH:
                return MacroRiskState(event.impact, Decimal("0.25"), True, "high_impact_event_window")
            if event.impact == NewsImpact.MEDIUM:
                return MacroRiskState(event.impact, Decimal("0.50"), False, "medium_impact_event_window")
        return MacroRiskState(event.impact, Decimal(1), False, "no_macro_restriction")
