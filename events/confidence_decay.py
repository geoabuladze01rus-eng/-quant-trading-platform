"""Time decay for news/event confidence; stale information loses influence."""
from decimal import Decimal
from math import exp, log


class ConfidenceDecay:
    def __init__(self,half_life_ms):
        if half_life_ms<=0: raise ValueError("half_life_ms must be positive")
        self.half_life_ms=half_life_ms
    def apply(self,confidence,age_ms):
        confidence=Decimal(str(confidence))
        if not 0<=confidence<=1 or age_ms<0: raise ValueError("invalid confidence or age")
        return confidence*Decimal(str(exp(-log(2)*age_ms/self.half_life_ms)))
