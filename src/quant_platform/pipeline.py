from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from .arbitrage import ArbitrageScanner
from .audit import AuditLog
from .domain import Quote
from .execution import PaperExecutionEngine
from .risk import RiskEngine
from .strategies.inter_exchange import InterExchangeArbitrageStrategy

@dataclass(slots=True)
class PaperArbitragePipeline:
    scanner: ArbitrageScanner
    risk: RiskEngine
    execution: PaperExecutionEngine
    audit: AuditLog
    strategy: InterExchangeArbitrageStrategy

    def run(self, quotes: list[Quote], portfolio_value: Decimal, quantity: Decimal) -> dict[str, object]:
        opportunity = self.scanner.scan(quotes, quantity)
        if opportunity is None:
            self.audit.record("strategy_no_trade", strategy=self.strategy.name,
                              symbol=quotes[0].symbol if quotes else None)
            return {"status": "no_trade", "reason": "no net-profitable opportunity"}

        self.audit.record("opportunity", net_edge_bps=str(opportunity.net_edge_bps),
                          symbol=opportunity.symbol)
        group = self.strategy.execution_group(opportunity)
        decision = self.risk.evaluate_group(group, portfolio_value)
        self.audit.record("risk_group_decision", approved=decision.approved,
                          reason=decision.reason, buy_venue=group.buy.venue.value,
                          sell_venue=group.sell.venue.value, quantity=str(group.quantity))
        if not decision.approved:
            return {"status": "rejected", "reason": decision.reason, "opportunity": opportunity}

        results = [self.execution.submit(group.buy, decision),
                   self.execution.submit(group.sell, decision)]
        if any(result["status"] == "rejected" for result in results):
            self.audit.record("execution_rejected", strategy=self.strategy.name)
            return {"status": "rejected", "results": results, "opportunity": opportunity}

        self.audit.record("paper_trade_accepted", strategy=self.strategy.name,
                          symbol=opportunity.symbol)
        return {"status": "paper_accepted", "results": results, "opportunity": opportunity}
