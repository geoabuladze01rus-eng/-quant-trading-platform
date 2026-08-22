"""Execution orchestrator: converts an approved TradeIntent into a controlled two-leg lifecycle."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
class OrchestratorState(str,Enum): IDLE="IDLE"; SUBMITTING="SUBMITTING"; RECONCILING="RECONCILING"; HEDGING="HEDGING"; COMPLETED="COMPLETED"; HALTED="HALTED"
@dataclass(frozen=True)
class ExecutionResult:
    state:OrchestratorState; buy_order_id:str|None; sell_order_id:str|None; hedge_required:bool; residual:Decimal; reason:str
class ExecutionOrchestrator:
    def __init__(self,router,lifecycle): self.router=router; self.lifecycle=lifecycle; self.state=OrchestratorState.IDLE
    async def execute(self,intent):
        start=self.lifecycle.start()
        if not start.allow_new_orders:
            self.state=OrchestratorState.HALTED; return ExecutionResult(self.state,None,None,False,Decimal(0),start.reason)
        self.state=OrchestratorState.SUBMITTING
        try:
            buy=await self.router.submit(intent.buy_venue,intent.idempotency_key+":buy",intent.buy_order)
            sell=await self.router.submit(intent.sell_venue,intent.idempotency_key+":sell",intent.sell_order)
        except Exception as exc:
            self.state=OrchestratorState.HALTED
            return ExecutionResult(self.state,None,None,True,Decimal(0),f"submission_failure:{type(exc).__name__}")
        self.state=OrchestratorState.RECONCILING
        d=self.lifecycle.reconcile(intent.quantity,intent.quantity,intent.quantity)
        if d.hedge_required:self.state=OrchestratorState.HEDGING
        else:self.state=d.state if d.state in (OrchestratorState.COMPLETED,) else OrchestratorState.RECONCILING
        return ExecutionResult(self.state,getattr(buy,"exchange_order_id",None),getattr(sell,"exchange_order_id",None),d.hedge_required,d.residual,d.reason)
