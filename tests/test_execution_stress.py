"""Stress scenarios for execution failure containment."""
import asyncio
from decimal import Decimal
from execution.reconciliation import FillReconciler,ReconciliationState

def test_partial_fill_creates_residual():
    r=FillReconciler().reconcile(Decimal("10"),Decimal("10"),Decimal("7"))
    assert r.state==ReconciliationState.RESIDUAL and r.hedge_required and r.residual==Decimal("3")

def test_overfill_is_failed():
    r=FillReconciler().reconcile(Decimal("10"),Decimal("11"),Decimal("10"))
    assert r.state==ReconciliationState.FAILED

def test_tolerance_allows_balanced_fills():
    r=FillReconciler().reconcile(Decimal("10"),Decimal("10"),Decimal("9.999"),Decimal("0.001"))
    assert r.state==ReconciliationState.BALANCED

async def _slow():
    await asyncio.sleep(0.001)

def test_async_timeout_surface():
    try: asyncio.run(asyncio.wait_for(_slow(),timeout=0.00001))
    except TimeoutError: return
    assert False,"timeout must surface to execution supervisor"
