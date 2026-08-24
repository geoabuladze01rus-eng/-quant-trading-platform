"""Fee/slippage-aware cross-venue arbitrage opportunity model."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class VenueQuote:
    venue:str; bid:Decimal; ask:Decimal; taker_fee_bps:Decimal
@dataclass(frozen=True)
class ArbitrageOpportunity:
    buy_venue:str; sell_venue:str; gross_edge_bps:Decimal; total_cost_bps:Decimal; net_edge_bps:Decimal; executable:bool
class OpportunityScanner:
    def __init__(self,min_net_edge_bps=Decimal(5),estimated_slippage_bps=Decimal(2)):
        self.min_net_edge_bps=Decimal(str(min_net_edge_bps)); self.estimated_slippage_bps=Decimal(str(estimated_slippage_bps))
    def scan(self,quotes):
        best=None
        for buy in quotes:
            for sell in quotes:
                if buy.venue==sell.venue or buy.ask<=0: continue
                gross=(sell.bid/buy.ask-1)*Decimal(10000)
                costs=buy.taker_fee_bps+sell.taker_fee_bps+self.estimated_slippage_bps*2
                net=gross-costs; candidate=ArbitrageOpportunity(buy.venue,sell.venue,gross,costs,net,net>=self.min_net_edge_bps)
                if best is None or candidate.net_edge_bps>best.net_edge_bps: best=candidate
        return best
