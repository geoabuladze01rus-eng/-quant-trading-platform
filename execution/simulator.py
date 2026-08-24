"""Deterministic execution simulator for paper/backtest integration tests."""
from dataclasses import dataclass
from decimal import Decimal
from random import Random


@dataclass(frozen=True)
class ExecutionRequest:
    side: str
    quantity: Decimal
    reference_price: Decimal

@dataclass(frozen=True)
class ExecutionResult:
    filled_quantity: Decimal
    fill_price: Decimal
    fee: Decimal
    latency_ms: int
    rejected: bool
    reason: str

class ExecutionSimulator:
    def __init__(self, fee_rate=Decimal("0.001"), slippage_bps=Decimal(2), rejection_rate=0.0, latency_ms=25, seed=7):
        if not 0 <= rejection_rate <= 1: raise ValueError("rejection_rate must be 0..1")
        self.fee_rate=Decimal(str(fee_rate)); self.slippage_bps=Decimal(str(slippage_bps)); self.rejection_rate=rejection_rate; self.latency_ms=latency_ms; self.rng=Random(seed)
    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        q=Decimal(str(request.quantity)); p=Decimal(str(request.reference_price))
        if q <= 0 or p <= 0: raise ValueError("quantity and reference_price must be positive")
        if self.rng.random() < self.rejection_rate: return ExecutionResult(Decimal(0),p,Decimal(0),self.latency_ms,True,"simulated_rejection")
        direction=Decimal(1) + self.slippage_bps/Decimal(10000)
        fill=p*direction if request.side.upper()=="BUY" else p/direction
        fee=q*fill*self.fee_rate
        return ExecutionResult(q,fill,fee,self.latency_ms,False,"filled")
