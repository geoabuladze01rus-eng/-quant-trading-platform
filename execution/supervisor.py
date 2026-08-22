"""Central execution supervisor for deterministic failure containment."""
from dataclasses import dataclass
from enum import Enum
class SupervisorState(str,Enum): READY="READY"; DEGRADED="DEGRADED"; HALTED="HALTED"
@dataclass(frozen=True)
class SupervisorDecision:
    state:SupervisorState; allow_execution:bool; cancel_new_orders:bool; require_hedge:bool; reason:str
class ExecutionSupervisor:
    def __init__(self,max_failures:int=3): self.max_failures=max_failures; self.failures=0; self.state=SupervisorState.READY
    def observe(self,exchange_healthy:bool,timeout:bool,execution_failure:bool,residual:bool)->SupervisorDecision:
        if not exchange_healthy or residual:
            self.state=SupervisorState.DEGRADED
            return SupervisorDecision(self.state,False,True,residual,"exchange_or_residual_risk")
        if timeout or execution_failure:self.failures+=1
        if self.failures>=self.max_failures:
            self.state=SupervisorState.HALTED
            return SupervisorDecision(self.state,False,True,False,"failure_threshold")
        if timeout or execution_failure:
            self.state=SupervisorState.DEGRADED
            return SupervisorDecision(self.state,False,True,False,"execution_failure")
        self.state=SupervisorState.READY
        return SupervisorDecision(self.state,True,False,False,"OK")
    def reset(self)->None:self.failures=0; self.state=SupervisorState.READY
