"""Execution-cost model for net arbitrage edge."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class CostEstimate:
    gross_edge_bps:Decimal; fees_bps:Decimal; slippage_bps:Decimal; fixed_cost_bps:Decimal; net_edge_bps:Decimal; executable:bool; reason:str
class CostEngine:
    def estimate(self,buy_price,sell_price,buy_fee_bps,sell_fee_bps,buy_avg_price,sell_avg_price,min_edge_bps,notional=0,fixed_cost=0):
        bp=Decimal(str(buy_price)); sp=Decimal(str(sell_price)); ba=Decimal(str(buy_avg_price)); sa=Decimal(str(sell_avg_price)); n=Decimal(str(notional)); fixed=Decimal(str(fixed_cost))
        if bp<=0 or sp<=0 or n<0:return CostEstimate(Decimal(0),Decimal(0),Decimal(0),Decimal(0),Decimal(0),False,"invalid_inputs")
        fees=Decimal(str(buy_fee_bps))+Decimal(str(sell_fee_bps)); gross=(sp-bp)/bp*Decimal(10000)
        slip=((ba-bp)/bp+(sp-sa)/sp)*Decimal(10000); fixed_bps=(fixed/n)*Decimal(10000) if n>0 else Decimal(0)
        net=gross-fees-slip-fixed_bps; ok=net>=Decimal(str(min_edge_bps))
        return CostEstimate(gross,fees,slip,fixed_bps,net,ok,"approved" if ok else "net_edge_below_threshold")
