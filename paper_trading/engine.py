"""Deterministic paper-trading engine for end-to-end strategy validation."""
from dataclasses import dataclass
from decimal import Decimal
@dataclass(frozen=True)
class PaperOrder:
    order_id:str; symbol:str; side:str; quantity:Decimal; price:Decimal
@dataclass(frozen=True)
class PaperFill:
    order_id:str; quantity:Decimal; price:Decimal; fee:Decimal
class PaperTradingEngine:
    def __init__(self,initial_cash:Decimal,fee_bps:Decimal=Decimal("5")):
        self.cash=Decimal(str(initial_cash)); self.fee_bps=Decimal(str(fee_bps)); self.positions={}; self.fills=[]
    def execute(self,order:PaperOrder)->PaperFill:
        q=Decimal(str(order.quantity)); p=Decimal(str(order.price)); fee=q*p*self.fee_bps/Decimal("10000")
        if q<=0 or p<=0: raise ValueError("quantity and price must be positive")
        if order.side.upper()=="BUY":
            cost=q*p+fee
            if cost>self.cash: raise ValueError("insufficient_cash")
            self.cash-=cost; self.positions[order.symbol]=self.positions.get(order.symbol,Decimal(0))+q
        elif order.side.upper()=="SELL":
            if q>self.positions.get(order.symbol,Decimal(0)): raise ValueError("insufficient_position")
            self.positions[order.symbol]-=q; self.cash+=q*p-fee
        else: raise ValueError("unsupported_side")
        fill=PaperFill(order.order_id,q,p,fee); self.fills.append(fill); return fill
    def equity(self,marks:dict[str,Decimal])->Decimal:
        return self.cash+sum((self.positions.get(s,Decimal(0))*Decimal(str(px)) for s,px in marks.items()),Decimal(0))
