"""Dynamic position sizing with hard portfolio, liquidity and volatility caps."""
from dataclasses import dataclass
from decimal import Decimal
@dataclass(frozen=True)
class SizeDecision:
    allowed:Decimal; notional:Decimal; reason:str
class DynamicPositionSizer:
    def size(self,requested_qty,price,depth_qty,equity,trade_pct,asset_pct,net_edge_bps,min_edge_bps,volatility=Decimal("0"),target_vol=Decimal("0"),vol_cap=Decimal("1")):
        q=Decimal(str(requested_qty)); p=Decimal(str(price)); e=Decimal(str(equity)); depth=Decimal(str(depth_qty)); edge=Decimal(str(net_edge_bps)); minimum=Decimal(str(min_edge_bps));
        if q<=0 or p<=0 or e<=0:return SizeDecision(Decimal(0),Decimal(0),"invalid_inputs")
        if edge<minimum:return SizeDecision(Decimal(0),Decimal(0),"edge_below_threshold")
        cap=min(q,depth,e*Decimal(str(trade_pct))/Decimal(100),e*Decimal(str(asset_pct))/Decimal(100)/p)
        v=Decimal(str(volatility)); tv=Decimal(str(target_vol)); vc=Decimal(str(vol_cap))
        if v>0 and tv>0:cap*=min(Decimal(1),tv/v)
        cap=min(cap,depth*vc)
        return SizeDecision(max(Decimal(0),cap),max(Decimal(0),cap)*p,"sized")
