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

    def run(
        self,
        quotes: list[Quote],
        portfolio_value: Decimal,
        quantity: Decimal,
    ) -> dict[str, object]:
        opportunity = self.scanner.scan(quotes, quantity)
        if opportunity is None:
            self.audit.record(
                "strategy_no_trade",
                strategy=self.strategy.name,
                symbol=quotes[0].symbol if quotes else None,
            )
            return {"status": "no_trade", "reason": "no net-profitable opportunity"}

        self.audit.record(
            "opportunity",
            net_edge_bps=str(opportunity.net_edge_bps),
            symbol=opportunity.symbol,
        )
        results: list[dict[str, str]] = []
        for intent in self.strategy.intents(opportunity):
            decision = self.risk.evaluate(intent, portfolio_value)
            self.audit.record(
                "risk_decision",
                venue=intent.venue.value,
                side=intent.side.value,
                approved=decision.approved,
                reason=decision.reason,
            )
            result = self.execution.submit(intent, decision)
            results.append(result)
            if result["status"] == "rejected":
                self.audit.record(
                    "execution_rejected",
                    venue=intent.venue.value,
                    reason=decision.reason,
                )
                return {
                    "status": "rejected",
                    "results": results,
                    "opportunity": opportunity,
                }

        self.audit.record(
            "paper_trade_accepted",
            strategy=self.strategy.name,
            symbol=opportunity.symbol,
        )
        return {
            "status": "paper_accepted",
            "results": results,
            "opportunity": opportunity,
        }
