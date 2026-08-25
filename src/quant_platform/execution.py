from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from .domain import OrderIntent, Venue
from .execution_orchestrator import (
    ExecutionOrchestrator,
    GroupReconciliation,
    OrderCloseReason,
)
from .risk import RiskDecision


@dataclass(slots=True)
class PaperExecutionEngine:
    """Safety-first executor. Live exchange calls are intentionally not implemented yet."""

    orchestrator: ExecutionOrchestrator = field(default_factory=ExecutionOrchestrator)
    max_residual_hedge_notional: Decimal = Decimal(10000)
    max_residual_hedge_slippage_bps: Decimal = Decimal(30)

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

    def process_fill(
        self,
        execution_id: str,
        *,
        fill_id: str,
        quantity: Decimal,
        price: Decimal,
    ) -> dict[str, str]:
        event = self.orchestrator.process_fill(
            execution_id,
            fill_id=fill_id,
            quantity=quantity,
            price=price,
        )
        return {
            "execution_id": execution_id,
            "event_id": event.event_id,
            "fill_id": event.fill_id or "",
            "state": event.state.value,
            "fill_quantity": str(event.fill_quantity),
            "fill_price": str(event.fill_price),
            "cumulative_filled_quantity": str(event.cumulative_filled_quantity),
            "remaining_quantity": str(event.remaining_quantity),
            "average_fill_price": str(event.average_fill_price),
            "correlation_id": event.correlation_id or "",
            "execution_group_id": event.execution_group_id or "",
        }

    def reconcile_group(
        self,
        execution_group_id: str,
        *,
        tolerance: Decimal = Decimal(0),
    ) -> GroupReconciliation:
        return self.orchestrator.reconcile_group(
            execution_group_id,
            tolerance=tolerance,
        )

    def close_order(
        self,
        execution_id: str,
        reason: OrderCloseReason,
        *,
        message: str | None = None,
    ) -> dict[str, str]:
        event = self.orchestrator.close_order(
            execution_id,
            reason,
            message=message,
        )
        return {
            "execution_id": execution_id,
            "event_id": event.event_id,
            "state": event.state.value,
            "message": event.message,
            "correlation_id": event.correlation_id or "",
            "execution_group_id": event.execution_group_id or "",
        }

    def hedge_residual(
        self,
        execution_group_id: str,
        *,
        venue: Venue,
        fill_id: str,
        price: Decimal,
        reference_price: Decimal,
    ) -> GroupReconciliation:
        return self.orchestrator.execute_paper_residual_hedge(
            execution_group_id,
            venue=venue,
            fill_id=fill_id,
            price=price,
            reference_price=reference_price,
            max_notional=self.max_residual_hedge_notional,
            max_slippage_bps=self.max_residual_hedge_slippage_bps,
        )
