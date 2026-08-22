"""Single decision pipeline: opportunity -> cost -> risk -> execution approval."""
from dataclasses import dataclass
from decimal import Decimal
from arbitrage.opportunity_engine import Opportunity, OpportunityEngine
from execution.cost_model import ExecutionCosts, ExecutionCostModel
from risk.exposure_guard import ExposureGuard, ExposureLimits, ExposureSnapshot
from risk.drawdown_controller import DrawdownController

@dataclass(frozen=True)
class PipelineDecision:
    accepted: bool
    net_edge_bps: Decimal
    reason: str
    risk_state: str

class ArbitrageDecisionPipeline:
    def __init__(self, opportunity_engine=None, cost_model=None, exposure_guard=None, drawdown_controller=None):
        self.opportunity_engine=opportunity_engine or OpportunityEngine()
        self.cost_model=cost_model or ExecutionCostModel()
        self.exposure_guard=exposure_guard or ExposureGuard()
        self.drawdown_controller=drawdown_controller or DrawdownController()

    def evaluate(self, opportunity: Opportunity, costs: ExecutionCosts, snapshot: ExposureSnapshot,
                 limits: ExposureLimits, equity: Decimal, high_watermark: Decimal) -> PipelineDecision:
        dd=self.drawdown_controller.evaluate(equity, high_watermark)
        if not dd.allow_new_positions:
            return PipelineDecision(False, Decimal(str(opportunity.gross_edge_bps))-sum(costs.__dict__.values(),Decimal(0)), "risk_state:"+dd.reason, dd.state.value)
        cost=self.cost_model.evaluate(opportunity.gross_edge_bps,costs)
        if not cost.executable:
            return PipelineDecision(False,cost.net_edge_bps,"cost_gate",dd.state.value)
        exposure=self.exposure_guard.check(snapshot,limits,opportunity.notional)
        if not exposure.allowed:
            return PipelineDecision(False,cost.net_edge_bps,"exposure:"+exposure.reason,dd.state.value)
        decision=self.opportunity_engine.evaluate(opportunity)
        return PipelineDecision(decision.accepted,decision.net_edge_bps,decision.reason,dd.state.value)
