"""Order-book depth execution estimator with slippage and fillability gates."""
from dataclasses import dataclass
from decimal import Decimal

from market.data_aggregator import BookLevel


@dataclass(frozen=True)
class DepthEstimate:
    requested_qty:Decimal; executable_qty:Decimal; average_price:Decimal; slippage_bps:Decimal; fully_executable:bool
class OrderBookDepthAnalyzer:
    def estimate(self,levels:tuple[BookLevel,...],quantity:Decimal,side:str)->DepthEstimate:
        q=Decimal(str(quantity)); remaining=q; notional=Decimal(0); best=None; filled=Decimal(0)
        if q<=0:return DepthEstimate(q,Decimal(0),Decimal(0),Decimal(0),False)
        for level in levels:
            p=Decimal(str(level.price)); available=Decimal(str(level.quantity)); take=min(remaining,available)
            if take<=0 or p<=0: continue
            if best is None: best=p
            filled+=take; notional+=take*p; remaining-=take
            if remaining<=0: break
        avg=notional/filled if filled else Decimal(0); slip=abs((avg/best-1)*Decimal(10000)) if best else Decimal(0)
        return DepthEstimate(q,filled,avg,slip,filled>=q)
