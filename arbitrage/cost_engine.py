"""Execution-cost model for net arbitrage edge."""
from dataclasses import dataclass
from decimal import Decimal
@dataclass(frozen=True)
class CostEstimate:
    gross_edge_bps:Decimal; fees_bps:Decimal; slippage_bps:Decimal; net_edge_bps:Decimal; executable:bool; reason:str
class CostEngine:
    def estimate(self,buy_price,sell_price,buy_fee_bps,sell_fee_bps,buy_avg_price,sell_avg_price,min_edge_bps):
        bp=Decimal(str(buy_price)); sp=Decimal(str(sell_price)); ba=Decimal(str(buy_avg_price)); sa=Decimal(str(sell_avg_price)); fees=Decimal(str(buy_fee_bps))+Decimal(str(sell_fee_bps));
        gross=(sp-bp)/bp*Decimal(10000) if bp>0 else Decimal(0)
        slip=((ba-bp)/bp+(sp-sa)/sp)*Decimal(10000) if bp>0 and sp>0 else Decimal(0)
        net=gross-fees-slip; ok=net>=Decimal(str(min_edge_bps))
        return CostEstimate(gross,fees,slip,net,ok,"approved" if ok else "net_edge_below_threshold")
