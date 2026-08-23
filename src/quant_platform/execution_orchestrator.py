from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
from uuid import uuid4
from .domain import OrderIntent
from .risk import RiskDecision
class ExecutionState(StrEnum):
    CREATED="created"; RISK_REJECTED="risk_rejected"; SUBMITTED="submitted"; PARTIALLY_FILLED="partially_filled"; FILLED="filled"; RECONCILING="reconciling"; HEDGE_REQUIRED="hedge_required"; COMPLETED="completed"; HALTED="halted"
@dataclass(frozen=True, slots=True)
class ExecutionEvent:
    event_id:str; execution_id:str; state:ExecutionState; message:str
@dataclass(slots=True)
class ExecutionOrchestrator:
    """Canonical safety-first lifecycle for one paper execution leg."""
    def start(self,intent:OrderIntent,risk:RiskDecision)->tuple[str,tuple[ExecutionEvent,...]]:
        execution_id=uuid4().hex
        if not risk.approved:return execution_id,(ExecutionEvent(uuid4().hex,execution_id,ExecutionState.RISK_REJECTED,risk.reason),)
        return execution_id,(ExecutionEvent(uuid4().hex,execution_id,ExecutionState.SUBMITTED,"paper order submitted"),)
    def transition(self,execution_id:str,state:ExecutionState,message:str)->ExecutionEvent:return ExecutionEvent(uuid4().hex,execution_id,state,message)
