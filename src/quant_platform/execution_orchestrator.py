from __future__ import annotations

from collections.abc import Mapping
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
    CANCELED = "canceled"
    EXPIRED = "expired"
    RECONCILING = "reconciling"
    HEDGE_REQUIRED = "hedge_required"
    COMPLETED = "completed"
    HALTED = "halted"


class ExecutionRole(StrEnum):
    PRIMARY = "primary"
    RESIDUAL_HEDGE = "residual_hedge"


class OrderCloseReason(StrEnum):
    CANCELED = "canceled"
    EXPIRED = "expired"


class GroupReconciliationState(StrEnum):
    BALANCED = "balanced"
    HEDGE_REQUIRED = "hedge_required"
    HEDGED = "hedged"
    HALTED = "halted"


class UnknownExecutionError(KeyError):
    """Raised when a lifecycle operation references an unknown execution."""


class InvalidExecutionTransition(ValueError):
    """Raised when an execution attempts to skip or leave a terminal state."""


class InvalidFillError(ValueError):
    """Raised when a fill cannot be applied to an execution safely."""


class ConflictingFillError(InvalidFillError):
    """Raised when a fill identifier is reused with different economics."""


class InvalidExecutionGroupError(ValueError):
    """Raised when a two-leg execution group is incomplete or inconsistent."""


class InvalidCheckpointError(ValueError):
    """Raised when persisted canonical execution state fails integrity checks."""


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
    execution_role: ExecutionRole = ExecutionRole.PRIMARY


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
    execution_role: ExecutionRole


@dataclass(frozen=True, slots=True)
class ExecutionGroupSnapshot:
    execution_group_id: str
    execution_ids: tuple[str, ...]
    states: tuple[ExecutionState, ...]
    submitted_at: datetime
    reconciled: bool


@dataclass(frozen=True, slots=True)
class ResidualExposure:
    symbol: str
    signed_quantity: Decimal
    hedge_side: Side
    hedge_quantity: Decimal


@dataclass(frozen=True, slots=True)
class GroupReconciliation:
    execution_group_id: str
    state: GroupReconciliationState
    buy_execution_id: str
    sell_execution_id: str
    target_quantity: Decimal
    buy_filled_quantity: Decimal
    sell_filled_quantity: Decimal
    matched_quantity: Decimal
    residual: ResidualExposure | None
    hedge_execution_id: str | None
    post_hedge_residual_quantity: Decimal
    message: str

    @property
    def hedge_required(self) -> bool:
        return self.state is GroupReconciliationState.HEDGE_REQUIRED


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
    execution_role: ExecutionRole
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
                ExecutionState.CANCELED,
                ExecutionState.EXPIRED,
                ExecutionState.HALTED,
            }
        ),
        ExecutionState.PARTIALLY_FILLED: frozenset(
            {
                ExecutionState.PARTIALLY_FILLED,
                ExecutionState.FILLED,
                ExecutionState.CANCELED,
                ExecutionState.EXPIRED,
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
        ExecutionState.CANCELED: frozenset(
            {ExecutionState.RECONCILING, ExecutionState.HALTED}
        ),
        ExecutionState.EXPIRED: frozenset(
            {ExecutionState.RECONCILING, ExecutionState.HALTED}
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
    _group_legs: dict[str, list[str]] = field(default_factory=dict, init=False, repr=False)
    _group_reconciliations: dict[str, GroupReconciliation] = field(
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
        execution_role: ExecutionRole = ExecutionRole.PRIMARY,
    ) -> tuple[str, tuple[ExecutionEvent, ...]]:
        role = ExecutionRole(execution_role)
        if execution_group_id is not None and not execution_group_id.strip():
            raise InvalidExecutionGroupError("execution_group_id must be non-empty")
        if risk.approved and execution_group_id is not None and role is ExecutionRole.PRIMARY:
            self._validate_new_group_leg(execution_group_id, intent)

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
            execution_role=role,
        )
        event = self._event(execution_id, context, initial_state, message)
        context.events.append(event)
        self._executions[execution_id] = context
        if risk.approved and execution_group_id is not None and role is ExecutionRole.PRIMARY:
            self._group_legs.setdefault(execution_group_id, []).append(execution_id)
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
        if not fill_quantity.is_finite() or not fill_price.is_finite():
            raise InvalidFillError("fill quantity and price must be finite")
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

    def close_order(
        self,
        execution_id: str,
        reason: OrderCloseReason,
        *,
        message: str | None = None,
    ) -> ExecutionEvent:
        """Record a terminal venue outcome before group reconciliation."""
        context = self._context(execution_id)
        close_reason = OrderCloseReason(reason)
        target_state = ExecutionState(close_reason.value)
        if context.state is target_state:
            return context.events[-1]
        if context.state not in {
            ExecutionState.SUBMITTED,
            ExecutionState.PARTIALLY_FILLED,
        }:
            raise InvalidExecutionTransition(
                f"cannot close order while execution is {context.state.value}"
            )
        return self.transition(
            execution_id,
            target_state,
            message or f"paper order {target_state.value}",
        )

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
            execution_role=context.execution_role,
        )

    def group_snapshots(self) -> tuple[ExecutionGroupSnapshot, ...]:
        """Expose immutable primary-leg status for recovery and timeout control."""
        snapshots: list[ExecutionGroupSnapshot] = []
        for group_id, execution_ids in sorted(self._group_legs.items()):
            contexts = [self._context(execution_id) for execution_id in execution_ids]
            snapshots.append(
                ExecutionGroupSnapshot(
                    execution_group_id=group_id,
                    execution_ids=tuple(execution_ids),
                    states=tuple(context.state for context in contexts),
                    submitted_at=max(context.events[0].timestamp for context in contexts),
                    reconciled=group_id in self._group_reconciliations,
                )
            )
        return tuple(snapshots)

    def export_checkpoint(self) -> dict[str, object]:
        """Return a deterministic JSON-safe snapshot of canonical execution state."""
        from .execution_checkpoint import export_checkpoint

        return export_checkpoint(self)

    @classmethod
    def from_checkpoint(
        cls,
        payload: Mapping[str, object],
    ) -> ExecutionOrchestrator:
        """Restore canonical state after validating the complete checkpoint first."""
        from .execution_checkpoint import restore_checkpoint

        return restore_checkpoint(payload)

    def reconcile_group(
        self,
        execution_group_id: str,
        *,
        tolerance: Decimal = Decimal(0),
    ) -> GroupReconciliation:
        """Finalize two primary legs and expose any signed residual position."""
        existing = self._group_reconciliations.get(execution_group_id)
        if existing is not None:
            return existing

        allowed_tolerance = Decimal(str(tolerance))
        if not allowed_tolerance.is_finite() or allowed_tolerance < 0:
            raise InvalidExecutionGroupError("reconciliation tolerance cannot be negative")

        buy_execution_id, buy_context, sell_execution_id, sell_context = (
            self._primary_group_contexts(execution_group_id)
        )
        buy_filled = buy_context.filled_quantity
        sell_filled = sell_context.filled_quantity
        signed_residual = buy_filled - sell_filled
        matched_quantity = min(buy_filled, sell_filled)
        target_quantity = buy_context.intent.quantity

        message = (
            f"two-leg reconciliation: buy_filled={buy_filled}, "
            f"sell_filled={sell_filled}, residual={signed_residual}"
        )
        self._begin_group_reconciliation(
            buy_execution_id,
            sell_execution_id,
            message,
        )

        residual = None
        if abs(signed_residual) > allowed_tolerance:
            residual = ResidualExposure(
                symbol=buy_context.intent.symbol,
                signed_quantity=signed_residual,
                hedge_side=Side.SELL if signed_residual > 0 else Side.BUY,
                hedge_quantity=abs(signed_residual),
            )
            self.transition(
                buy_execution_id,
                ExecutionState.HEDGE_REQUIRED,
                message,
            )
            self.transition(
                sell_execution_id,
                ExecutionState.HEDGE_REQUIRED,
                message,
            )
            state = GroupReconciliationState.HEDGE_REQUIRED
        else:
            self.transition(buy_execution_id, ExecutionState.COMPLETED, message)
            self.transition(sell_execution_id, ExecutionState.COMPLETED, message)
            state = GroupReconciliationState.BALANCED

        result = GroupReconciliation(
            execution_group_id=execution_group_id,
            state=state,
            buy_execution_id=buy_execution_id,
            sell_execution_id=sell_execution_id,
            target_quantity=target_quantity,
            buy_filled_quantity=buy_filled,
            sell_filled_quantity=sell_filled,
            matched_quantity=matched_quantity,
            residual=residual,
            hedge_execution_id=None,
            post_hedge_residual_quantity=signed_residual,
            message=message,
        )
        self._group_reconciliations[execution_group_id] = result
        return result

    def execute_paper_residual_hedge(
        self,
        execution_group_id: str,
        *,
        venue: Venue,
        fill_id: str,
        price: Decimal,
        reference_price: Decimal,
        max_notional: Decimal,
        max_slippage_bps: Decimal,
    ) -> GroupReconciliation:
        """Flatten a reconciled residual using a capped, immediately filled paper order."""
        reconciliation = self._group_reconciliations.get(execution_group_id)
        if reconciliation is None:
            raise InvalidExecutionGroupError("execution group must be reconciled before hedging")
        if reconciliation.state in {
            GroupReconciliationState.HEDGED,
            GroupReconciliationState.HALTED,
        }:
            return reconciliation
        if not reconciliation.hedge_required or reconciliation.residual is None:
            raise InvalidExecutionGroupError("execution group has no hedgeable residual")
        if not fill_id:
            raise InvalidFillError("fill_id must be non-empty")

        hedge_venue = Venue(venue)
        _, buy_context, _, sell_context = self._primary_group_contexts(execution_group_id)
        if hedge_venue not in {buy_context.intent.venue, sell_context.intent.venue}:
            raise InvalidExecutionGroupError("residual hedge venue must belong to the execution group")

        hedge_price = Decimal(str(price))
        market_reference = Decimal(str(reference_price))
        notional_limit = Decimal(str(max_notional))
        slippage_limit = Decimal(str(max_slippage_bps))
        if not all(
            value.is_finite()
            for value in (
                hedge_price,
                market_reference,
                notional_limit,
                slippage_limit,
            )
        ):
            raise InvalidExecutionGroupError("hedge limits and prices must be finite")
        if hedge_price <= 0 or market_reference <= 0:
            raise InvalidExecutionGroupError("hedge and reference prices must be positive")
        if notional_limit <= 0:
            raise InvalidExecutionGroupError("max hedge notional must be positive")
        if slippage_limit < 0:
            raise InvalidExecutionGroupError("max hedge slippage cannot be negative")

        residual = reconciliation.residual
        hedge_notional = residual.hedge_quantity * hedge_price
        adverse_slippage_bps = self._adverse_slippage_bps(
            residual.hedge_side,
            hedge_price,
            market_reference,
        )
        if hedge_notional > notional_limit:
            return self._halt_group(reconciliation, "residual hedge notional limit exceeded")
        if adverse_slippage_bps > slippage_limit:
            return self._halt_group(reconciliation, "residual hedge slippage limit exceeded")

        hedge_intent = OrderIntent(
            venue=hedge_venue,
            symbol=residual.symbol,
            side=residual.hedge_side,
            quantity=residual.hedge_quantity,
            limit_price=hedge_price,
            strategy="residual_hedge",
            reason=f"flatten residual for execution group {execution_group_id}",
        )
        hedge_execution_id, _ = self.start(
            hedge_intent,
            RiskDecision(True, "risk-reducing paper hedge"),
            correlation_id=f"{execution_group_id}:residual-hedge",
            execution_group_id=execution_group_id,
            execution_role=ExecutionRole.RESIDUAL_HEDGE,
        )
        self.process_fill(
            hedge_execution_id,
            fill_id=fill_id,
            quantity=residual.hedge_quantity,
            price=hedge_price,
        )
        self.transition(
            hedge_execution_id,
            ExecutionState.RECONCILING,
            "residual hedge filled",
        )
        self.transition(
            hedge_execution_id,
            ExecutionState.COMPLETED,
            "residual exposure flattened in paper execution",
        )
        self.transition(
            reconciliation.buy_execution_id,
            ExecutionState.COMPLETED,
            "residual exposure flattened in paper execution",
        )
        self.transition(
            reconciliation.sell_execution_id,
            ExecutionState.COMPLETED,
            "residual exposure flattened in paper execution",
        )
        result = GroupReconciliation(
            execution_group_id=execution_group_id,
            state=GroupReconciliationState.HEDGED,
            buy_execution_id=reconciliation.buy_execution_id,
            sell_execution_id=reconciliation.sell_execution_id,
            target_quantity=reconciliation.target_quantity,
            buy_filled_quantity=reconciliation.buy_filled_quantity,
            sell_filled_quantity=reconciliation.sell_filled_quantity,
            matched_quantity=reconciliation.matched_quantity,
            residual=residual,
            hedge_execution_id=hedge_execution_id,
            post_hedge_residual_quantity=Decimal(0),
            message="residual exposure flattened in paper execution",
        )
        self._group_reconciliations[execution_group_id] = result
        return result

    def _context(self, execution_id: str) -> _ExecutionContext:
        try:
            return self._executions[execution_id]
        except KeyError as exc:
            raise UnknownExecutionError(execution_id) from exc

    def _validate_new_group_leg(self, execution_group_id: str, intent: OrderIntent) -> None:
        execution_ids = self._group_legs.get(execution_group_id, [])
        if len(execution_ids) >= 2:
            raise InvalidExecutionGroupError("execution group already has two primary legs")
        if not execution_ids:
            return

        existing = self._context(execution_ids[0]).intent
        if intent.symbol != existing.symbol:
            raise InvalidExecutionGroupError("execution group legs must use the same symbol")
        if intent.quantity != existing.quantity:
            raise InvalidExecutionGroupError("execution group legs must use equal quantities")
        if intent.side is existing.side:
            raise InvalidExecutionGroupError("execution group requires opposite sides")
        if intent.venue is existing.venue:
            raise InvalidExecutionGroupError("execution group requires distinct venues")

    def _primary_group_contexts(
        self,
        execution_group_id: str,
    ) -> tuple[str, _ExecutionContext, str, _ExecutionContext]:
        execution_ids = self._group_legs.get(execution_group_id, [])
        if len(execution_ids) != 2:
            raise InvalidExecutionGroupError("execution group must contain exactly two primary legs")

        first_id, second_id = execution_ids
        first = self._context(first_id)
        second = self._context(second_id)
        if first.intent.side is Side.BUY:
            return first_id, first, second_id, second
        return second_id, second, first_id, first

    def _begin_group_reconciliation(
        self,
        buy_execution_id: str,
        sell_execution_id: str,
        message: str,
    ) -> None:
        for execution_id in (buy_execution_id, sell_execution_id):
            state = self.current_state(execution_id)
            if state not in {
                ExecutionState.FILLED,
                ExecutionState.CANCELED,
                ExecutionState.EXPIRED,
            }:
                raise InvalidExecutionTransition(
                    f"cannot reconcile execution before order closure: {state.value}"
                )
        self.transition(buy_execution_id, ExecutionState.RECONCILING, message)
        self.transition(sell_execution_id, ExecutionState.RECONCILING, message)

    def _halt_group(
        self,
        reconciliation: GroupReconciliation,
        message: str,
    ) -> GroupReconciliation:
        self.transition(
            reconciliation.buy_execution_id,
            ExecutionState.HALTED,
            message,
        )
        self.transition(
            reconciliation.sell_execution_id,
            ExecutionState.HALTED,
            message,
        )
        result = GroupReconciliation(
            execution_group_id=reconciliation.execution_group_id,
            state=GroupReconciliationState.HALTED,
            buy_execution_id=reconciliation.buy_execution_id,
            sell_execution_id=reconciliation.sell_execution_id,
            target_quantity=reconciliation.target_quantity,
            buy_filled_quantity=reconciliation.buy_filled_quantity,
            sell_filled_quantity=reconciliation.sell_filled_quantity,
            matched_quantity=reconciliation.matched_quantity,
            residual=reconciliation.residual,
            hedge_execution_id=None,
            post_hedge_residual_quantity=reconciliation.post_hedge_residual_quantity,
            message=message,
        )
        self._group_reconciliations[reconciliation.execution_group_id] = result
        return result

    @staticmethod
    def _adverse_slippage_bps(side: Side, price: Decimal, reference: Decimal) -> Decimal:
        if side is Side.BUY:
            return max(Decimal(0), (price - reference) / reference * Decimal(10000))
        return max(Decimal(0), (reference - price) / reference * Decimal(10000))

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
            execution_role=context.execution_role,
        )
