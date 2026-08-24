"""Unified arbitrage execution lifecycle coordinating state, reconciliation, hedge and supervisor."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class LifecycleState(str,Enum): READY="READY"; EXECUTING="EXECUTING"; RECONCILING="RECONCILING"; HEDGING="HEDGING"; COMPLETED="COMPLETED"; HALTED="HALTED"
@dataclass(frozen=True)
class LifecycleDecision:
    state:LifecycleState; allow_new_orders:bool; hedge_required:bool; residual:Decimal; reason:str
class ExecutionLifecycle:
    def __init__(self,supervisor,reconciler,hedge_manager): self.supervisor=supervisor; self.reconciler=reconciler; self.hedge_manager=hedge_manager; self.state=LifecycleState.READY
    def start(self,exchange_healthy=True):
        d=self.supervisor.observe(exchange_healthy,False,False,False)
        self.state=LifecycleState.EXECUTING if d.allow_execution else LifecycleState.HALTED
        return LifecycleDecision(self.state,d.allow_execution,False,Decimal(0),d.reason)
    def reconcile(self,target,buy_filled,sell_filled,tolerance=Decimal(0)):
        self.state=LifecycleState.RECONCILING
        r=self.reconciler.reconcile(target,buy_filled,sell_filled,tolerance)
        if r.hedge_required:
            self.state=LifecycleState.HEDGING
            return LifecycleDecision(self.state,False,True,r.residual,r.reason)
        self.state=LifecycleState.COMPLETED if r.state.value=="BALANCED" else LifecycleState.RECONCILING
        return LifecycleDecision(self.state,self.state==LifecycleState.COMPLETED,False,r.residual,r.reason)
