"""Dynamic arbitrage position sizing from depth, edge and portfolio limits."""
from dataclasses import dataclass
from decimal import Decimal
@dataclass(frozen=True)
class PositionSize:
    requested:Decimal; allowed:Decimal; risk_notional:Decimal; reason:str
class DynamicPositionSizer:
    def size(self,requested_qty:Decimal,price:Decimal,available_depth_qty:Decimal,equity:Decimal,max_trade_pct:Decimal,max_asset_pct:Decimal,net_edge_bps:Decimal,min_edge_bps:Decimal)->PositionSize:
        q=Decimal(str(requested_qty)); p=Decimal(str(price)); eq=Decimal(str(equity)); depth=Decimal(str(available_depth_qty)); edge=Decimal(str(net_edge_bps))
        if min(q, p, eq, depth)<=0 or edge<Decimal(str(min_edge_bps)): return PositionSize(q,Decimal(0),Decimal(0),"edge_or_input_limit")
        max_notional=min(eq*Decimal(str(max_trade_pct))/100,eq*Decimal(str(max_asset_pct))/100)
        allowed=min(q,depth,max_notional/p)
        return PositionSize(q,allowed,allowed*p,"approved" if allowed>0 else "portfolio_limit")
