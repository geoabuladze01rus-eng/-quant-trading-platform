from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import ClassVar
from uuid import uuid4

from .domain import OrderIntent, Side, Venue
from .risk import RiskDecision


def _utc_now() -> datetime:
    return datetime.now(UTC)


class ExecutionState(StrEnum):
    CREATED = "created"
    RISK_REJECTED = "risk_rejected"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    RECONCILING = "reconciling"
    HEDGE_REQUIRED = "hedge_required"
    COMPLETED = "completed"
    HALTED = "halted"


class UnknownExecutionError(KeyError):
    """Raised when a lifecycle operation references an unknown execution."""


class InvalidExecutionTransition(ValueError):
    """Raised when an execution attempts to skip or leave a terminal state."""


@dataclass(frozen=True, slots=True)
class ExecutionEvent:
    event_id: str
    execution_id: str
    state: ExecutionState
    message: str
    timestamp: datetime = field(default_factory=_utc_now)
    venue: Venue | None = None
    symbol: str | None = None
    side: Side | None = None
    quantity: Decimal | None = None
    correlation_id: str | None = None
    execution_group_id: str | None = None


@dataclass(slots=True)
class _ExecutionContext:
    intent: OrderIntent
    state: ExecutionState
    correlation_id: str
    execution_group_id: str | None
    events: list[ExecutionEvent] = field(default_factory=list)


@dataclass(slots=True)
class ExecutionOrchestrator:
    """Canonical safety-first lifecycle for one paper execution leg."""

    _ALLOWED_TRANSITIONS: ClassVar[dict[ExecutionState, frozenset[ExecutionState]]] = {
        ExecutionState.CREATED: frozenset(
            {ExecutionState.RISK_REJECTED, ExecutionState.SUBMITTED}
        ),
        ExecutionState.RISK_REJECTED: frozenset(),
        ExecutionState.SUBMITTED: frozenset(
            {
                ExecutionState.PARTIALLY_FILLED,
                ExecutionState.FILLED,
                ExecutionState.HALTED,
            }
        ),
        ExecutionState.PARTIALLY_FILLED: frozenset(
            {
                ExecutionState.PARTIALLY_FILLED,
                ExecutionState.FILLED,
                ExecutionState.RECONCILING,
                ExecutionState.HEDGE_REQUIRED,
                ExecutionState.HALTED,
            }
        ),
        ExecutionState.FILLED: frozenset(
            {
                ExecutionState.RECONCILING,
                ExecutionState.COMPLETED,
                ExecutionState.HALTED,
            }
        ),
        ExecutionState.RECONCILING: frozenset(
            {
                ExecutionState.HEDGE_REQUIRED,
                ExecutionState.COMPLETED,
                ExecutionState.HALTED,
            }
        ),
        ExecutionState.HEDGE_REQUIRED: frozenset(
            {ExecutionState.COMPLETED, ExecutionState.HALTED}
        ),
        ExecutionState.COMPLETED: frozenset(),
        ExecutionState.HALTED: frozenset(),
    }

    _executions: dict[str, _ExecutionContext] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )

    def start(
        self,
        intent: OrderIntent,
        risk: RiskDecision,
        *,
        correlation_id: str | None = None,
        execution_group_id: str | None = None,
    ) -> tuple[str, tuple[ExecutionEvent, ...]]:
        execution_id = uuid4().hex
        initial_state = (
            ExecutionState.SUBMITTED if risk.approved else ExecutionState.RISK_REJECTED
        )
        message = "paper order submitted" if risk.approved else risk.reason
        context = _ExecutionContext(
            intent=intent,
            state=initial_state,
            correlation_id=correlation_id or uuid4().hex,
            execution_group_id=execution_group_id,
        )
        event = self._event(execution_id, context, initial_state, message)
        context.events.append(event)
        self._executions[execution_id] = context
        return execution_id, (event,)

    def transition(
        self,
        execution_id: str,
        state: ExecutionState,
        message: str,
    ) -> ExecutionEvent:
        context = self._context(execution_id)
        target_state = ExecutionState(state)
        allowed = self._ALLOWED_TRANSITIONS[context.state]
        if target_state not in allowed:
            raise InvalidExecutionTransition(
                f"invalid execution transition: {context.state.value} -> {target_state.value}"
            )

        context.state = target_state
        event = self._event(execution_id, context, target_state, message)
        context.events.append(event)
        return event

    def current_state(self, execution_id: str) -> ExecutionState:
        return self._context(execution_id).state

    def events(self, execution_id: str) -> tuple[ExecutionEvent, ...]:
        return tuple(self._context(execution_id).events)

    def _context(self, execution_id: str) -> _ExecutionContext:
        try:
            return self._executions[execution_id]
        except KeyError as exc:
            raise UnknownExecutionError(execution_id) from exc

    @staticmethod
    def _event(
        execution_id: str,
        context: _ExecutionContext,
        state: ExecutionState,
        message: str,
    ) -> ExecutionEvent:
        intent = context.intent
        return ExecutionEvent(
            event_id=uuid4().hex,
            execution_id=execution_id,
            state=state,
            message=message,
            venue=intent.venue,
            symbol=intent.symbol,
            side=intent.side,
            quantity=intent.quantity,
            correlation_id=context.correlation_id,
            execution_group_id=context.execution_group_id,
        )
