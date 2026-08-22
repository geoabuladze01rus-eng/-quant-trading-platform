"""Execution router facade combining risk approval with idempotent intent reservation."""
from dataclasses import dataclass
from execution.idempotency import IdempotencyRegistry, IntentStatus
@dataclass(frozen=True)
class RouteResult:
    intent_id:str; submitted:bool; duplicate:bool; reason:str
class IdempotentRouter:
    def __init__(self,risk_gate,connector,registry=None): self.risk_gate=risk_gate; self.connector=connector; self.registry=registry or IdempotencyRegistry()
    async def submit(self,intent_id,request):
        existing=self.registry.reserve(intent_id,getattr(request,'strategy_id','unknown'),getattr(request,'leg_id',intent_id))
        if existing.status!=IntentStatus.NEW:return RouteResult(intent_id,False,True,"already_reserved")
        if not self.risk_gate.approve(request): self.registry.transition(intent_id,IntentStatus.FAILED); return RouteResult(intent_id,False,False,"risk_rejected")
        try:
            result=await self.connector.submit(request); exchange_id=getattr(result,'order_id',None) or getattr(result,'id',None); self.registry.transition(intent_id,IntentStatus.SUBMITTED,exchange_id); return RouteResult(intent_id,True,False,"submitted")
        except Exception:
            self.registry.transition(intent_id,IntentStatus.FAILED); raise
