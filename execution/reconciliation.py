"""Reconcile actual fills of both arbitrage legs and expose residual risk."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
class ReconciliationState(str,Enum): PENDING="PENDING"; BALANCED="BALANCED"; RESIDUAL="RESIDUAL"; FAILED="FAILED"
@dataclass(frozen=True)
class Reconciliation:
    state:ReconciliationState; buy_filled:Decimal; sell_filled:Decimal; residual:Decimal; hedge_required:bool; reason:str
class FillReconciler:
    def reconcile(self,target_qty:Decimal,buy_filled:Decimal,sell_filled:Decimal,tolerance:Decimal=Decimal("0"))->Reconciliation:
        target=Decimal(str(target_qty)); buy=max(Decimal(0),Decimal(str(buy_filled))); sell=max(Decimal(0),Decimal(str(sell_filled))); residual=buy-sell; tolerance=max(Decimal(0),Decimal(str(tolerance)))
        if buy>target or sell>target:return Reconciliation(ReconciliationState.FAILED,buy,sell,residual,True,"overfill")
        if abs(residual)<=tolerance and buy>=target-tolerance and sell>=target-tolerance:return Reconciliation(ReconciliationState.BALANCED,buy,sell,residual,False,"balanced")
        if residual!=0:return Reconciliation(ReconciliationState.RESIDUAL,buy,sell,residual,True,"unhedged_residual")
        return Reconciliation(ReconciliationState.PENDING,buy,sell,residual,False,"awaiting_fills")
