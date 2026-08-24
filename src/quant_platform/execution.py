from __future__ import annotations

from dataclasses import dataclass, field

from .domain import OrderIntent
from .execution_orchestrator import ExecutionOrchestrator
from .risk import RiskDecision


@dataclass(slots=True)
class PaperExecutionEngine:
    """Safety-first executor. Live exchange calls are intentionally not implemented yet."""

    orchestrator: ExecutionOrchestrator = field(default_factory=ExecutionOrchestrator)

    def submit(
        self,
        intent: OrderIntent,
        risk: RiskDecision,
        *,
        correlation_id: str | None = None,
        execution_group_id: str | None = None,
    ) -> dict[str, str]:
        execution_id, events = self.orchestrator.start(
            intent,
            risk,
            correlation_id=correlation_id,
            execution_group_id=execution_group_id,
        )
        event = events[0]
        result = {
            "execution_id": execution_id,
            "event_id": event.event_id,
            "state": event.state.value,
            "correlation_id": event.correlation_id or "",
        }
        if event.execution_group_id is not None:
            result["execution_group_id"] = event.execution_group_id

        if not risk.approved:
            result.update({"status": "rejected", "reason": risk.reason})
            return result

        result.update(
            {
                "status": "paper_accepted",
                "venue": intent.venue.value,
                "symbol": intent.symbol,
                "side": intent.side.value,
                "strategy": intent.strategy,
            }
        )
        return result
