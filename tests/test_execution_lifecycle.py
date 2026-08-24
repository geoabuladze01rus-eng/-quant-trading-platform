"""Integration tests for the unified execution lifecycle."""
from decimal import Decimal

from execution.lifecycle import ExecutionLifecycle, LifecycleState
from execution.reconciliation import FillReconciler
from execution.supervisor import ExecutionSupervisor


class Hedge:
    def plan(self,*args): return None
def make(): return ExecutionLifecycle(ExecutionSupervisor(),FillReconciler(),Hedge())
def test_balanced_lifecycle():
    x=make(); assert x.start().state==LifecycleState.EXECUTING
    d=x.reconcile(Decimal(10),Decimal(10),Decimal(10)); assert d.state==LifecycleState.COMPLETED and not d.hedge_required
def test_partial_lifecycle_requires_hedge():
    x=make(); x.start(); d=x.reconcile(Decimal(10),Decimal(10),Decimal(7)); assert d.state==LifecycleState.HEDGING and d.hedge_required and d.residual==Decimal(3)
def test_unhealthy_exchange_halts():
    x=make(); d=x.start(exchange_healthy=False); assert d.state==LifecycleState.HALTED and not d.allow_new_orders
