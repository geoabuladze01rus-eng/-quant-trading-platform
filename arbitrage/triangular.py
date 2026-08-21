"""Three-leg triangular arbitrage scanner with fee-aware executable edge."""
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class TriangleMarket:
    symbol: str
    bid: Decimal
    ask: Decimal
    fee_bps: Decimal

@dataclass(frozen=True)
class TriangleOpportunity:
    path: tuple[str,str,str]
    start_amount: Decimal
    end_amount: Decimal
    net_return_bps: Decimal
    executable: bool

class TriangularArbitrageScanner:
    def __init__(self,min_net_edge_bps=Decimal("5")):
        self.min_net_edge_bps=Decimal(str(min_net_edge_bps))
    def scan(self,start_asset,start_amount,markets):
        m={x.symbol:x for x in markets}; amount=Decimal(str(start_amount)); candidates=[]
        for ab in m.values():
            if not ab.symbol.startswith(start_asset+"/") or ab.ask<=0: continue
            b=ab.symbol.split("/")[1]
            for bc in m.values():
                if not bc.symbol.startswith(b+"/") or bc.bid<=0: continue
                c=bc.symbol.split("/")[1]
                ca=m.get(c+"/"+start_asset)
                if not ca or ca.bid<=0: continue
                x=amount/ab.ask*(Decimal("1")-ab.fee_bps/Decimal("10000"))
                x*=bc.bid*(Decimal("1")-bc.fee_bps/Decimal("10000"))
                x*=ca.bid*(Decimal("1")-ca.fee_bps/Decimal("10000"))
                ret=(x/amount-1)*Decimal("10000")
                candidates.append(TriangleOpportunity((ab.symbol,bc.symbol,ca.symbol),amount,x,ret,ret>=self.min_net_edge_bps))
        return max(candidates,key=lambda x:x.net_return_bps) if candidates else None
