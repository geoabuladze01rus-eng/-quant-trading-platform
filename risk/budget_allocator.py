"""Portfolio-level risk budget allocator for concurrent arbitrage opportunities."""
from dataclasses import dataclass
from decimal import Decimal
@dataclass(frozen=True)
class BudgetCandidate:
    id:str; score:Decimal; notional:Decimal; risk_weight:Decimal; correlation_penalty:Decimal=Decimal("0")
@dataclass(frozen=True)
class Allocation:
    id:str; notional:Decimal; fraction_of_budget:Decimal
class RiskBudgetAllocator:
    def allocate(self,candidates:list[BudgetCandidate],total_budget:Decimal,max_daily_loss:Decimal)->list[Allocation]:
        budget=min(Decimal(str(total_budget)),Decimal(str(max_daily_loss)))
        ranked=sorted(candidates,key=lambda c:Decimal(str(c.score))/max(Decimal("0.000001"),Decimal(str(c.risk_weight))+Decimal(str(c.correlation_penalty)),reverse=True)
        selected=[]; remaining=budget
        for c in ranked:
            if remaining<=0: break
            risk=max(Decimal("0.000001"),Decimal(str(c.risk_weight))+Decimal(str(c.correlation_penalty))); capacity=min(Decimal(str(c.notional)),remaining/risk)
            if capacity<=0: continue
            selected.append((c.id,capacity)); remaining-=capacity*risk
        total=sum((x[1] for x in selected),Decimal(0)); return [Allocation(cid,n,n/total if total else Decimal(0)) for cid,n in selected]
