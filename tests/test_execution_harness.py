"""Deterministic execution harness tests for safe testnet rollout."""
from dataclasses import dataclass
from decimal import Decimal
@dataclass
class Result: submitted:bool; exchange_order_id:str
class FakeAdapter:
    def __init__(self,fail=False): self.fail=fail; self.calls=0
    async def submit(self,order):
        self.calls+=1
        if self.fail: raise RuntimeError("simulated exchange failure")
        return Result(True,f"ex-{self.calls}")
async def test_idempotent_retry():
    from execution.idempotent_router import IdempotentRouter
    class RiskGate:
        def approve(self, order): return True
    adapter=FakeAdapter(); router=IdempotentRouter(RiskGate(),adapter); order=object()
    a=await router.submit("arb-1",order); b=await router.submit("arb-1",order)
    assert a.submitted and b.duplicate and adapter.calls==1
async def test_two_leg_failure_requires_hedge():
    from execution.two_leg_manager import TwoLegExecutionManager
    class Router:
        def __init__(self): self.n=0
        async def submit(self,*args): self.n+=1; return Result(self.n==1,f"ex-{self.n}")
    hedges=[]
    async def hedge(order,qty): hedges.append((order,qty))
    result=await TwoLegExecutionManager(Router(),hedge).execute("b",object(),"s",object(),Decimal("1"))
    assert result.reason=="sell_leg_rejected" and hedges
