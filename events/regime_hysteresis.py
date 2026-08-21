"""Hysteresis filter preventing regime flapping on noisy inputs."""
from dataclasses import dataclass

@dataclass(frozen=True)
class RegimeState:
    regime: str
    consecutive: int

class RegimeHysteresis:
    def __init__(self, min_confirmations=3):
        if min_confirmations <= 0: raise ValueError("min_confirmations must be positive")
        self.min_confirmations=min_confirmations; self.current=None; self.candidate=None; self.count=0
    def update(self, proposed_regime):
        if not proposed_regime: raise ValueError("proposed_regime is required")
        if self.current is None:
            self.current=proposed_regime; self.candidate=None; self.count=0
            return RegimeState(self.current,self.count)
        if proposed_regime == self.current:
            self.candidate=None; self.count=0
            return RegimeState(self.current,self.count)
        if proposed_regime != self.candidate:
            self.candidate=proposed_regime; self.count=1
        else: self.count += 1
        if self.count >= self.min_confirmations:
            self.current=self.candidate; self.candidate=None; self.count=0
        return RegimeState(self.current,self.count)
