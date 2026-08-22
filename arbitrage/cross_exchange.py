"""Cross-exchange spot arbitrage evaluator with inventory and cost gates."""
from dataclasses import dataclass
from decimal import Decimal
@dataclass(frozen=True)
class VenueQuote:
    venue:str; bid:Decimal; ask:Decimal; executable_buy_qty:Decimal; executable_sell_qty:Decimal
@dataclass(frozen=True)
class CrossExchangeOpportunity:
    buy_venue:str; sell_venue:str; quantity:Decimal; gross_edge_bps:Decimal; net_edge_bps:Decimal; executable:bool
class CrossExchangeArbitrage:
    def evaluate(self,buy:VenueQuote,sell:VenueQuote,total_cost_bps:Decimal,min_net_edge_bps:Decimal=Decimal("2"))->CrossExchangeOpportunity:
        qty=min(Decimal(str(buy.executable_buy_qty)),Decimal(str(sell.executable_sell_qty)))
        if qty<=0 or buy.ask<=0:return CrossExchangeOpportunity(buy.venue,sell.venue,Decimal(0),Decimal(0),Decimal(0),False)
        gross=(Decimal(str(sell.bid))/Decimal(str(buy.ask))-1)*Decimal(10000); net=gross-Decimal(str(total_cost_bps))
        return CrossExchangeOpportunity(buy.venue,sell.venue,qty,gross,net,net>=Decimal(str(min_net_edge_bps)))
