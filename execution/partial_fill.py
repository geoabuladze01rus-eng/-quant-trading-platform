"""Deterministic partial-fill accounting and residual exposure calculation."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class FillUpdate:
    filled_qty:Decimal; fill_price:Decimal; fee:Decimal
@dataclass(frozen=True)
class FillState:
    requested_qty:Decimal; filled_qty:Decimal; remaining_qty:Decimal; avg_price:Decimal; total_fee:Decimal; complete:bool
class PartialFillTracker:
    def __init__(self,requested_qty:Decimal):
        self.requested=Decimal(str(requested_qty)); self.filled=Decimal(0); self.notional=Decimal(0); self.fee=Decimal(0)
    def apply(self,update:FillUpdate)->FillState:
        q=Decimal(str(update.filled_qty)); p=Decimal(str(update.fill_price)); fee=Decimal(str(update.fee))
        if q<=0 or p<=0 or self.filled+q>self.requested: raise ValueError("invalid_fill")
        self.filled+=q; self.notional+=q*p; self.fee+=fee; rem=self.requested-self.filled
        avg=self.notional/self.filled if self.filled else Decimal(0)
        return FillState(self.requested,self.filled,rem,avg,self.fee,rem==0)
