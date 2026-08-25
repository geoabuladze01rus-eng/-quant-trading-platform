from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from .execution import PaperExecutionEngine
from .execution_orchestrator import (
    ExecutionState,
    GroupReconciliation,
    OrderCloseReason,
)

_OPEN_ORDER_STATES = frozenset(
    {
        ExecutionState.SUBMITTED,
        ExecutionState.PARTIALLY_FILLED,
    }
)
_CLOSED_ORDER_STATES = frozenset(
    {
        ExecutionState.FILLED,
        ExecutionState.CANCELED,
        ExecutionState.EXPIRED,
    }
)


@dataclass(frozen=True, slots=True)
class TimeoutSweepResult:
    execution_group_id: str
    expired_execution_ids: tuple[str, ...]
    reconciliation: GroupReconciliation | None
    resulting_states: tuple[ExecutionState, ...]


@dataclass(slots=True)
class ExecutionTimeoutController:
    """Close stale paper legs and reconcile each complete group exactly once."""

    engine: PaperExecutionEngine
    timeout: timedelta = timedelta(seconds=5)

    def __post_init__(self) -> None:
        if self.timeout <= timedelta(0):
            raise ValueError("execution timeout must be positive")

    def sweep(self, *, now: datetime | None = None) -> tuple[TimeoutSweepResult, ...]:
        checked_at = now or datetime.now(UTC)
        if checked_at.tzinfo is None or checked_at.utcoffset() is None:
            raise ValueError("execution timeout timestamp must be timezone-aware")

        results: list[TimeoutSweepResult] = []
        for group in self.engine.orchestrator.group_snapshots():
            if group.reconciled:
                continue
            if checked_at - group.submitted_at < self.timeout:
                continue

            expired_execution_ids: list[str] = []
            for execution_id, state in zip(
                group.execution_ids,
                group.states,
                strict=True,
            ):
                if state not in _OPEN_ORDER_STATES:
                    continue
                self.engine.close_order(
                    execution_id,
                    OrderCloseReason.EXPIRED,
                    message="paper order expired after execution group timeout",
                )
                expired_execution_ids.append(execution_id)

            resulting_states = tuple(
                self.engine.orchestrator.current_state(execution_id)
                for execution_id in group.execution_ids
            )
            reconciliation = None
            if len(group.execution_ids) == 2 and all(
                state in _CLOSED_ORDER_STATES for state in resulting_states
            ):
                reconciliation = self.engine.reconcile_group(group.execution_group_id)
                resulting_states = tuple(
                    self.engine.orchestrator.current_state(execution_id)
                    for execution_id in group.execution_ids
                )

            if not expired_execution_ids and reconciliation is None:
                continue

            results.append(
                TimeoutSweepResult(
                    execution_group_id=group.execution_group_id,
                    expired_execution_ids=tuple(expired_execution_ids),
                    reconciliation=reconciliation,
                    resulting_states=resulting_states,
                )
            )
        return tuple(results)
