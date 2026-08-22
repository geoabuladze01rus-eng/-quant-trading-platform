"""Depth-aware arbitrage opportunity evaluation."""
from dataclasses import dataclass
from decimal import Decimal
from market.orderbook_depth import DepthEstimate
@dataclass(frozen=True)
class DepthOpportunity:
    symbol:str; buy_venue:str; sell_venue:str; requested_qty:Decimal; gross_edge_bps:Decimal; slippage_bps:Decimal; fees_bps:Decimal; net_edge_bps:Decimal; executable:bool; reason:str
class DepthOpportunityEngine:
    def evaluate(self,buy_venue:str,sell_venue:str,buy:DepthEstimate,sell:DepthEstimate,fees_bps:Decimal,min_net_edge_bps:Decimal=Decimal("2"))->DepthOpportunity:
        qty=min(buy.executable_qty,sell.executable_qty); fees=Decimal(str(fees_bps))
        if not buy.fully_executable or not sell.fully_executable:return DepthOpportunity("UNKNOWN",buy_venue,sell_venue,qty,Decimal(0),max(buy.slippage_bps,sell.slippage_bps),fees,Decimal(0),False,"insufficient_depth")
        gross=(sell.average_price/buy.average_price-1)*Decimal(10000); slip=buy.slippage_bps+sell.slippage_bps; net=gross-slip-fees; ok=net>=min_net_edge_bps
        return DepthOpportunity("UNKNOWN",buy_venue,sell_venue,qty,gross,slip,fees,net,ok,"approved" if ok else "insufficient_net_edge")
