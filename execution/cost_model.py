"""All-in execution cost model for arbitrage viability checks."""
from dataclasses import dataclass
from decimal import Decimal
@dataclass(frozen=True)
class ExecutionCosts:
    fee_bps:Decimal; spread_bps:Decimal; slippage_bps:Decimal; funding_bps:Decimal; latency_bps:Decimal; partial_fill_bps:Decimal=Decimal("0")
@dataclass(frozen=True)
class CostResult:
    gross_edge_bps:Decimal; total_cost_bps:Decimal; net_edge_bps:Decimal; executable:bool
class ExecutionCostModel:
    def evaluate(self,gross_edge_bps:Decimal,costs:ExecutionCosts,min_net_edge_bps:Decimal=Decimal("2"))->CostResult:
        gross=Decimal(str(gross_edge_bps)); total=sum((Decimal(str(x)) for x in costs.__dict__.values()),Decimal(0)); net=gross-total
        return CostResult(gross,total,net,net>=Decimal(str(min_net_edge_bps)))
