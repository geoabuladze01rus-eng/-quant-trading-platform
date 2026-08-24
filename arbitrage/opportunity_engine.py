"""Central opportunity pipeline: normalize edge, apply costs, risk and execution gates."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Opportunity: strategy:str; venue_buy:str; venue_sell:str; symbol:str; gross_edge_bps:Decimal; expected_cost_bps:Decimal; notional:Decimal
@dataclass(frozen=True)
class OpportunityDecision: accepted:bool; net_edge_bps:Decimal; reason:str
class OpportunityEngine:
    def evaluate(self,o:Opportunity,min_net_edge_bps:Decimal=Decimal(2),max_notional:Decimal|None=None)->OpportunityDecision:
        gross=Decimal(str(o.gross_edge_bps)); net=gross-Decimal(str(o.expected_cost_bps))
        if o.notional<=0:return OpportunityDecision(False,net,"invalid_notional")
        if max_notional is not None and o.notional>Decimal(str(max_notional)):return OpportunityDecision(False,net,"notional_limit")
        if net<Decimal(str(min_net_edge_bps)):return OpportunityDecision(False,net,"insufficient_net_edge")
        return OpportunityDecision(True,net,"approved")
