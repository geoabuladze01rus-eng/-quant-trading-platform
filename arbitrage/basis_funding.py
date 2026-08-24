"""Spot/futures basis and funding arbitrage evaluator."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class BasisQuote:
    venue:str; spot_price:Decimal; futures_price:Decimal; funding_rate_bps:Decimal; days_to_expiry:Decimal
@dataclass(frozen=True)
class BasisOpportunity:
    venue:str; annualized_basis_bps:Decimal; funding_bps:Decimal; net_edge_bps:Decimal; executable:bool
class BasisFundingArbitrage:
    def evaluate(self,q:BasisQuote,total_cost_bps:Decimal,min_net_edge_bps:Decimal=Decimal(2))->BasisOpportunity:
        spot=Decimal(str(q.spot_price)); fut=Decimal(str(q.futures_price)); days=Decimal(str(q.days_to_expiry))
        if spot<=0 or days<=0:return BasisOpportunity(q.venue,Decimal(0),Decimal(0),Decimal(0),False)
        basis=(fut/spot-1)*Decimal(10000); annual=basis*Decimal(365)/days; funding=Decimal(str(q.funding_rate_bps))*Decimal(365)/Decimal(8); net=annual+funding-Decimal(str(total_cost_bps))
        return BasisOpportunity(q.venue,annual,funding,net,net>=Decimal(str(min_net_edge_bps)))
