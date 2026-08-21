"""Risk-adjusted ranking of concurrent arbitrage opportunities."""
from dataclasses import dataclass
from decimal import Decimal
@dataclass(frozen=True)
class Candidate:
    id:str; net_edge_bps:Decimal; fill_probability:Decimal; liquidity_score:Decimal; latency_score:Decimal; hedge_risk:Decimal
@dataclass(frozen=True)
class RankedCandidate:
    id:str; score:Decimal; rank:int
class OpportunityRanker:
    def rank(self,candidates:list[Candidate])->list[RankedCandidate]:
        scored=[]
        for c in candidates:
            edge=max(Decimal(0),Decimal(str(c.net_edge_bps)))/Decimal(100)
            score=edge*Decimal(str(c.fill_probability))*Decimal(str(c.liquidity_score))*Decimal(str(c.latency_score))*(Decimal(1)-Decimal(str(c.hedge_risk)))
            scored.append((c.id,score))
        scored.sort(key=lambda x:x[1],reverse=True)
        return [RankedCandidate(cid,score,i+1) for i,(cid,score) in enumerate(scored)]
