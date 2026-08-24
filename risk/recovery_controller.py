"""Controlled recovery after a portfolio risk-off event."""
from dataclasses import dataclass
from enum import Enum


class RecoveryState(str,Enum): LOCKED="LOCKED"; COOLDOWN="COOLDOWN"; PROBATION="PROBATION"; ACTIVE="ACTIVE"
@dataclass(frozen=True)
class RecoveryDecision:
    state:RecoveryState; allow_new_positions:bool; reason:str
class RecoveryController:
    def __init__(self,cooldown_cycles:int=10,probation_cycles:int=25): self.cooldown_cycles=cooldown_cycles; self.probation_cycles=probation_cycles; self.state=RecoveryState.LOCKED; self.cycles=0
    def tick(self,risk_off:bool,healthy_feeds:int,min_healthy_feeds:int=2)->RecoveryDecision:
        if risk_off or healthy_feeds<min_healthy_feeds: self.state=RecoveryState.LOCKED; self.cycles=0; return RecoveryDecision(self.state,False,"risk_or_feed_not_ready")
        self.cycles+=1
        if self.state==RecoveryState.LOCKED:self.state=RecoveryState.COOLDOWN; self.cycles=1
        elif self.state==RecoveryState.COOLDOWN and self.cycles>=self.cooldown_cycles:self.state=RecoveryState.PROBATION; self.cycles=0
        elif self.state==RecoveryState.PROBATION and self.cycles>=self.probation_cycles:self.state=RecoveryState.ACTIVE; self.cycles=0
        return RecoveryDecision(self.state,self.state==RecoveryState.ACTIVE,self.state.value.lower())
