"""Depth-aware arbitrage scanner across multiple order-book levels."""
from dataclasses import dataclass
from decimal import Decimal
@dataclass(frozen=True)
class Level: price: Decimal; quantity: Decimal
@dataclass(frozen=True)
class DepthOpportunity:
    buy_venue:str; sell_venue:str; quantity:Decimal; buy_notional:Decimal; sell_notional:Decimal; gross_profit:Decimal; total_cost:Decimal; net_profit:Decimal; net_edge_bps:Decimal; executable:bool
class DepthArbitrageScanner:
    def __init__(self,min_net_edge_bps=Decimal("5")): self.min_net_edge_bps=Decimal(str(min_net_edge_bps))
    def _consume(self,levels,q,buy):
        rem=q; notional=Decimal(0); filled=Decimal(0)
        for x in sorted(levels,key=lambda z:z.price,reverse=not buy):
            take=min(rem,x.quantity); notional+=take*x.price; filled+=take; rem-=take
            if rem<=0: break
        return notional,filled
    def scan(self,buy_venue,sell_venue,asks,bids,max_quantity,fee_buy_bps,fee_sell_bps):
        q=Decimal(str(max_quantity)); bc,bq=self._consume(asks,q,True); sv,sq=self._consume(bids,q,False); qty=min(bq,sq)
        if qty<=0: return DepthOpportunity(buy_venue,sell_venue,Decimal(0),Decimal(0),Decimal(0),Decimal(0),Decimal(0),Decimal(0),Decimal(0),False)
        bc,_=self._consume(asks,qty,True); sv,_=self._consume(bids,qty,False)
        fees=bc*Decimal(str(fee_buy_bps))/10000+sv*Decimal(str(fee_sell_bps))/10000; net=sv-bc-fees; edge=net/bc*10000 if bc else Decimal(0)
        return DepthOpportunity(buy_venue,sell_venue,qty,bc,sv,sv-bc,fees,net,edge,net>0 and edge>=self.min_net_edge_bps)
