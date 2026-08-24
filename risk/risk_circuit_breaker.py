"""Portfolio circuit breaker coordinating daily loss, drawdown and feed health."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class CircuitState(str,Enum): ARMED="ARMED"; TRIPPED="TRIPPED"; RECOVERY="RECOVERY"
@dataclass(frozen=True)
class CircuitDecision:
    state:CircuitState; allow_new_orders:bool; force_unwind:bool; reason:str
class RiskCircuitBreaker:
    def __init__(self): self.state=CircuitState.ARMED
    def evaluate(self,daily_loss_pct:Decimal,drawdown_pct:Decimal,max_daily_loss_pct:Decimal,max_drawdown_pct:Decimal,healthy_venues:int,min_healthy_venues:int=1)->CircuitDecision:
        if daily_loss_pct>=max_daily_loss_pct or drawdown_pct>=max_drawdown_pct:
            self.state=CircuitState.TRIPPED; return CircuitDecision(self.state,False,True,"loss_limit")
        if healthy_venues<min_healthy_venues:
            self.state=CircuitState.TRIPPED; return CircuitDecision(self.state,False,False,"no_healthy_venue")
        if self.state==CircuitState.TRIPPED: self.state=CircuitState.RECOVERY; return CircuitDecision(self.state,False,False,"recovery_wait")
        if self.state==CircuitState.RECOVERY:return CircuitDecision(self.state,False,False,"recovery_wait")
        return CircuitDecision(CircuitState.ARMED,True,False,"OK")
    def reset(self)->None:self.state=CircuitState.ARMED
