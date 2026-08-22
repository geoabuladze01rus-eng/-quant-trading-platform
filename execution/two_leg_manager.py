"""Coordinated two-leg execution with partial-fill detection and hedge callback."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
class LegState(str,Enum): PENDING="PENDING"; SUBMITTED="SUBMITTED"; FILLED="FILLED"; HEDGING="HEDGING"; FAILED="FAILED"
@dataclass(frozen=True)
class TwoLegResult:
    state:LegState; buy_filled:Decimal; sell_filled:Decimal; residual:Decimal; reason:str
class TwoLegExecutionManager:
    def __init__(self,router,hedge): self.router=router; self.hedge=hedge
    async def execute(self,buy_intent,buy_request,sell_intent,sell_request,target_qty:Decimal)->TwoLegResult:
        b=await self.router.submit(buy_intent,buy_request)
        if not b.submitted:return TwoLegResult(LegState.FAILED,Decimal(0),Decimal(0),Decimal(target_qty),"buy_leg_rejected")
        s=await self.router.submit(sell_intent,sell_request)
        if not s.submitted:
            h=await self.hedge(buy_request,target_qty)
            return TwoLegResult(LegState.HEDGING,target_qty,Decimal(0),target_qty,"sell_leg_rejected")
        return TwoLegResult(LegState.SUBMITTED,Decimal(0),Decimal(0),Decimal(target_qty),"both_legs_submitted")
