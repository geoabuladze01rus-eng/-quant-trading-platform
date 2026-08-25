from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Self

from .domain import OrderIntent, Venue
from .execution_checkpoint import JsonExecutionCheckpointStore
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
    checkpoint_store: JsonExecutionCheckpointStore | None = None

    def __post_init__(self) -> None:
        self.max_residual_hedge_notional = Decimal(
            str(self.max_residual_hedge_notional)
        )
        self.max_residual_hedge_slippage_bps = Decimal(
            str(self.max_residual_hedge_slippage_bps)
        )
        if (
            not self.max_residual_hedge_notional.is_finite()
            or self.max_residual_hedge_notional <= 0
        ):
            raise ValueError("max residual hedge notional must be finite and positive")
        if (
            not self.max_residual_hedge_slippage_bps.is_finite()
            or self.max_residual_hedge_slippage_bps < 0
        ):
            raise ValueError("max residual hedge slippage must be finite and non-negative")

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

        self._persist_checkpoint()

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
        self._persist_checkpoint()
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
        reconciliation = self.orchestrator.reconcile_group(
            execution_group_id,
            tolerance=tolerance,
        )
        self._persist_checkpoint()
        return reconciliation

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
        self._persist_checkpoint()
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
        reconciliation = self.orchestrator.execute_paper_residual_hedge(
            execution_group_id,
            venue=venue,
            fill_id=fill_id,
            price=price,
            reference_price=reference_price,
            max_notional=self.max_residual_hedge_notional,
            max_slippage_bps=self.max_residual_hedge_slippage_bps,
        )
        self._persist_checkpoint()
        return reconciliation

    def export_checkpoint(self) -> dict[str, object]:
        return self.orchestrator.export_checkpoint()

    def save_checkpoint(self, store: JsonExecutionCheckpointStore) -> None:
        store.save(self.export_checkpoint())

    def _persist_checkpoint(self) -> None:
        if self.checkpoint_store is not None:
            self.save_checkpoint(self.checkpoint_store)

    @classmethod
    def from_checkpoint(
        cls,
        payload: Mapping[str, object],
        *,
        max_residual_hedge_notional: Decimal = Decimal(10000),
        max_residual_hedge_slippage_bps: Decimal = Decimal(30),
        checkpoint_store: JsonExecutionCheckpointStore | None = None,
    ) -> Self:
        return cls(
            orchestrator=ExecutionOrchestrator.from_checkpoint(payload),
            max_residual_hedge_notional=max_residual_hedge_notional,
            max_residual_hedge_slippage_bps=max_residual_hedge_slippage_bps,
            checkpoint_store=checkpoint_store,
        )

    @classmethod
    def from_checkpoint_store(
        cls,
        store: JsonExecutionCheckpointStore,
        *,
        max_residual_hedge_notional: Decimal = Decimal(10000),
        max_residual_hedge_slippage_bps: Decimal = Decimal(30),
    ) -> Self:
        return cls.from_checkpoint(
            store.load(),
            max_residual_hedge_notional=max_residual_hedge_notional,
            max_residual_hedge_slippage_bps=max_residual_hedge_slippage_bps,
            checkpoint_store=store,
        )
