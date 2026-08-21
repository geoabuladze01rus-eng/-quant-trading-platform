"""Translate external events into bounded market-impact and risk adjustments."""
from dataclasses import dataclass
from decimal import Decimal
from enum import IntEnum

class ImpactDirection(IntEnum):
    NEGATIVE = -1
    NEUTRAL = 0
    POSITIVE = 1

@dataclass(frozen=True)
class EventImpact:
    event_type: str
    asset: str
    direction: ImpactDirection
    confidence: Decimal
    severity: Decimal
    risk_multiplier: Decimal
    reason: str

class EventImpactEngine:
    def __init__(self, min_multiplier: Decimal = Decimal("0"), max_multiplier: Decimal = Decimal("1")):
        self.min_multiplier = min_multiplier
        self.max_multiplier = max_multiplier

    def evaluate(self, event_type: str, asset: str, direction: ImpactDirection, confidence: Decimal, severity: Decimal, reason: str = "") -> EventImpact:
        confidence = max(Decimal("0"), min(Decimal("1"), confidence))
        severity = max(Decimal("0"), min(Decimal("1"), severity))
        reduction = confidence * severity
        multiplier = self.max_multiplier - reduction
        multiplier = max(self.min_multiplier, min(self.max_multiplier, multiplier))
        return EventImpact(event_type, asset, direction, confidence, severity, multiplier, reason)
