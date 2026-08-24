"""Coordinated multi-leg execution with residual exposure and hedge actions."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class LegState(str,Enum): PENDING="PENDING"; PARTIAL="PARTIAL"; FILLED="FILLED"; CANCELED="CANCELED"; HEDGE_REQUIRED="HEDGE_REQUIRED"
@dataclass(frozen=True)
class Leg: id:str; target_qty:Decimal; filled_qty:Decimal=Decimal(0); state:LegState=LegState.PENDING
@dataclass(frozen=True)
class ExecutionDecision: state:str; residual_qty:Decimal; hedge_qty:Decimal; action:str
class MultiLegExecutor:
    def reconcile(self,legs:list[Leg])->ExecutionDecision:
        if not legs:return ExecutionDecision("INVALID",Decimal(0),Decimal(0),"reject")
        residual=max((Decimal(str(x.target_qty))-Decimal(str(x.filled_qty)) for x in legs),default=Decimal(0))
        if all(x.state==LegState.FILLED for x in legs):return ExecutionDecision("FILLED",Decimal(0),Decimal(0),"complete")
        partial=any(x.filled_qty>0 for x in legs)
        if partial and residual>0:return ExecutionDecision("HEDGE_REQUIRED",residual,residual,"hedge_or_unwind")
        return ExecutionDecision("PENDING",residual,Decimal(0),"continue")
