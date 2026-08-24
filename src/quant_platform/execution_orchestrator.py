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


class InvalidFillError(ValueError):
    """Raised when a fill cannot be applied to an execution safely."""


class ConflictingFillError(InvalidFillError):
    """Raised when a fill identifier is reused with different economics."""


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
    fill_id: str | None = None
    fill_quantity: Decimal | None = None
    fill_price: Decimal | None = None
    cumulative_filled_quantity: Decimal | None = None
    remaining_quantity: Decimal | None = None
    average_fill_price: Decimal | None = None


@dataclass(frozen=True, slots=True)
class ExecutionSnapshot:
    execution_id: str
    state: ExecutionState
    requested_quantity: Decimal
    filled_quantity: Decimal
    remaining_quantity: Decimal
    average_fill_price: Decimal | None
    correlation_id: str
    execution_group_id: str | None


@dataclass(frozen=True, slots=True)
class _FillRecord:
    quantity: Decimal
    price: Decimal
    event: ExecutionEvent


@dataclass(slots=True)
class _ExecutionContext:
    intent: OrderIntent
    state: ExecutionState
    correlation_id: str
    execution_group_id: str | None
    events: list[ExecutionEvent] = field(default_factory=list)
    fills: dict[str, _FillRecord] = field(default_factory=dict)
    filled_quantity: Decimal = Decimal(0)
    fill_notional: Decimal = Decimal(0)


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

    def process_fill(
        self,
        execution_id: str,
        *,
        fill_id: str,
        quantity: Decimal,
        price: Decimal,
    ) -> ExecutionEvent:
        """Apply one incremental fill exactly once and advance the leg lifecycle."""
        context = self._context(execution_id)
        fill_quantity = Decimal(str(quantity))
        fill_price = Decimal(str(price))
        if not fill_id:
            raise InvalidFillError("fill_id must be non-empty")
        if fill_quantity <= 0:
            raise InvalidFillError("fill quantity must be positive")
        if fill_price <= 0:
            raise InvalidFillError("fill price must be positive")

        existing = context.fills.get(fill_id)
        if existing is not None:
            if existing.quantity != fill_quantity or existing.price != fill_price:
                raise ConflictingFillError(
                    f"fill_id {fill_id!r} was already recorded with different values"
                )
            return existing.event

        if context.state not in {
            ExecutionState.SUBMITTED,
            ExecutionState.PARTIALLY_FILLED,
        }:
            raise InvalidExecutionTransition(
                f"cannot process fill while execution is {context.state.value}"
            )

        cumulative_quantity = context.filled_quantity + fill_quantity
        if cumulative_quantity > context.intent.quantity:
            raise InvalidFillError("cumulative fill quantity exceeds requested quantity")

        context.filled_quantity = cumulative_quantity
        context.fill_notional += fill_quantity * fill_price
        remaining_quantity = context.intent.quantity - cumulative_quantity
        state = (
            ExecutionState.FILLED
            if remaining_quantity == 0
            else ExecutionState.PARTIALLY_FILLED
        )
        context.state = state
        average_fill_price = context.fill_notional / cumulative_quantity
        event = self._event(
            execution_id,
            context,
            state,
            "paper order filled" if state is ExecutionState.FILLED else "paper order partially filled",
            fill_id=fill_id,
            fill_quantity=fill_quantity,
            fill_price=fill_price,
            cumulative_filled_quantity=cumulative_quantity,
            remaining_quantity=remaining_quantity,
            average_fill_price=average_fill_price,
        )
        context.events.append(event)
        context.fills[fill_id] = _FillRecord(fill_quantity, fill_price, event)
        return event

    def current_state(self, execution_id: str) -> ExecutionState:
        return self._context(execution_id).state

    def events(self, execution_id: str) -> tuple[ExecutionEvent, ...]:
        return tuple(self._context(execution_id).events)

    def snapshot(self, execution_id: str) -> ExecutionSnapshot:
        context = self._context(execution_id)
        average_fill_price = (
            context.fill_notional / context.filled_quantity
            if context.filled_quantity > 0
            else None
        )
        return ExecutionSnapshot(
            execution_id=execution_id,
            state=context.state,
            requested_quantity=context.intent.quantity,
            filled_quantity=context.filled_quantity,
            remaining_quantity=context.intent.quantity - context.filled_quantity,
            average_fill_price=average_fill_price,
            correlation_id=context.correlation_id,
            execution_group_id=context.execution_group_id,
        )

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
        *,
        fill_id: str | None = None,
        fill_quantity: Decimal | None = None,
        fill_price: Decimal | None = None,
        cumulative_filled_quantity: Decimal | None = None,
        remaining_quantity: Decimal | None = None,
        average_fill_price: Decimal | None = None,
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
            fill_id=fill_id,
            fill_quantity=fill_quantity,
            fill_price=fill_price,
            cumulative_filled_quantity=cumulative_filled_quantity,
            remaining_quantity=remaining_quantity,
            average_fill_price=average_fill_price,
        )
