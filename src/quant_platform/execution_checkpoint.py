"""Validated JSON-safe persistence for the canonical execution orchestrator."""
from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from .domain import OrderIntent, Side, Venue
from .execution_orchestrator import (
    ExecutionEvent,
    ExecutionOrchestrator,
    ExecutionRole,
    ExecutionState,
    GroupReconciliation,
    GroupReconciliationState,
    InvalidCheckpointError,
    ResidualExposure,
    _ExecutionContext,
    _FillRecord,
    _utc_now,
)

CHECKPOINT_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class JsonExecutionCheckpointStore:
    """Atomically persist validated canonical execution checkpoints as JSON."""

    path: Path

    def save(self, payload: Mapping[str, object]) -> None:
        restore_checkpoint(payload)
        serialized = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None
        try:
            descriptor, temporary_name = tempfile.mkstemp(
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
            )
            temporary_path = Path(temporary_name)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(serialized)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary_path, 0o600)
            os.replace(temporary_path, self.path)
            self._sync_parent_directory()
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    def load(self) -> dict[str, object]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise InvalidCheckpointError("cannot read execution checkpoint") from exc
        checkpoint = dict(_mapping(payload, "checkpoint"))
        restore_checkpoint(checkpoint)
        return checkpoint

    def _sync_parent_directory(self) -> None:
        descriptor = os.open(
            self.path.parent,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
        )
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def export_checkpoint(orchestrator: ExecutionOrchestrator) -> dict[str, object]:
    return {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "created_at": _utc_now().isoformat(),
        "executions": [
            _serialize_execution(execution_id, context)
            for execution_id, context in sorted(orchestrator._executions.items())
        ],
        "group_legs": {
            group_id: list(execution_ids)
            for group_id, execution_ids in sorted(orchestrator._group_legs.items())
        },
        "group_reconciliations": [
            _serialize_reconciliation(reconciliation)
            for _, reconciliation in sorted(orchestrator._group_reconciliations.items())
        ],
    }


def restore_checkpoint(payload: Mapping[str, object]) -> ExecutionOrchestrator:
    try:
        return _restore_checkpoint(_mapping(payload, "checkpoint"))
    except InvalidCheckpointError:
        raise
    except (InvalidOperation, KeyError, TypeError, ValueError) as exc:
        raise InvalidCheckpointError("invalid canonical execution checkpoint") from exc


def _restore_checkpoint(payload: Mapping[str, Any]) -> ExecutionOrchestrator:
    version = payload.get("schema_version")
    if version != CHECKPOINT_SCHEMA_VERSION:
        raise InvalidCheckpointError(f"unsupported checkpoint schema version: {version!r}")
    _timestamp(payload.get("created_at"), "created_at")

    orchestrator = ExecutionOrchestrator()
    executions = _list(payload.get("executions"), "executions")
    for item in executions:
        execution_id, context = _deserialize_execution(_mapping(item, "execution"))
        if execution_id in orchestrator._executions:
            raise InvalidCheckpointError(f"duplicate execution_id: {execution_id}")
        orchestrator._executions[execution_id] = context

    group_legs = _mapping(payload.get("group_legs"), "group_legs")
    registered_primary_ids: set[str] = set()
    for group_id, raw_execution_ids in sorted(group_legs.items()):
        if not isinstance(group_id, str) or not group_id:
            raise InvalidCheckpointError("checkpoint contains an empty execution group id")
        execution_ids = _list(raw_execution_ids, f"group_legs.{group_id}")
        if not 1 <= len(execution_ids) <= 2:
            raise InvalidCheckpointError("execution group must contain one or two primary legs")
        for raw_execution_id in execution_ids:
            execution_id = _required_str(raw_execution_id, "execution_id")
            if execution_id in registered_primary_ids:
                raise InvalidCheckpointError("primary execution is registered more than once")
            group_context = orchestrator._executions.get(execution_id)
            if group_context is None:
                raise InvalidCheckpointError("execution group references an unknown execution")
            if group_context.execution_group_id != group_id:
                raise InvalidCheckpointError("execution group id does not match execution metadata")
            if group_context.execution_role is not ExecutionRole.PRIMARY:
                raise InvalidCheckpointError("execution group contains a non-primary execution")
            orchestrator._validate_new_group_leg(group_id, group_context.intent)
            orchestrator._group_legs.setdefault(group_id, []).append(execution_id)
            registered_primary_ids.add(execution_id)

    for execution_id, context in orchestrator._executions.items():
        should_be_registered = (
            context.execution_group_id is not None
            and context.execution_role is ExecutionRole.PRIMARY
            and context.state is not ExecutionState.RISK_REJECTED
        )
        if should_be_registered != (execution_id in registered_primary_ids):
            raise InvalidCheckpointError("primary execution group registration is inconsistent")

    reconciliations = _list(
        payload.get("group_reconciliations"),
        "group_reconciliations",
    )
    referenced_hedges: set[str] = set()
    for item in reconciliations:
        reconciliation = _deserialize_reconciliation(_mapping(item, "reconciliation"))
        group_id = reconciliation.execution_group_id
        if group_id in orchestrator._group_reconciliations:
            raise InvalidCheckpointError(f"duplicate group reconciliation: {group_id}")
        _validate_reconciliation(orchestrator, reconciliation)
        orchestrator._group_reconciliations[group_id] = reconciliation
        if reconciliation.hedge_execution_id is not None:
            referenced_hedges.add(reconciliation.hedge_execution_id)

    all_hedges = {
        execution_id
        for execution_id, context in orchestrator._executions.items()
        if context.execution_role is ExecutionRole.RESIDUAL_HEDGE
    }
    if all_hedges != referenced_hedges:
        raise InvalidCheckpointError("residual hedge references are inconsistent")
    return orchestrator


def _serialize_execution(
    execution_id: str,
    context: _ExecutionContext,
) -> dict[str, object]:
    intent = context.intent
    return {
        "execution_id": execution_id,
        "intent": {
            "venue": intent.venue.value,
            "symbol": intent.symbol,
            "side": intent.side.value,
            "quantity": str(intent.quantity),
            "limit_price": _string_decimal(intent.limit_price),
            "strategy": intent.strategy,
            "reason": intent.reason,
        },
        "state": context.state.value,
        "correlation_id": context.correlation_id,
        "execution_group_id": context.execution_group_id,
        "execution_role": context.execution_role.value,
        "events": [_serialize_event(event) for event in context.events],
        "fills": [
            {
                "fill_id": fill_id,
                "quantity": str(record.quantity),
                "price": str(record.price),
                "event_id": record.event.event_id,
            }
            for fill_id, record in sorted(context.fills.items())
        ],
    }


def _deserialize_execution(
    payload: Mapping[str, Any],
) -> tuple[str, _ExecutionContext]:
    execution_id = _required_str(payload.get("execution_id"), "execution_id")
    intent_payload = _mapping(payload.get("intent"), "intent")
    intent = OrderIntent(
        venue=Venue(_required_str(intent_payload.get("venue"), "intent.venue")),
        symbol=_required_str(intent_payload.get("symbol"), "intent.symbol"),
        side=Side(_required_str(intent_payload.get("side"), "intent.side")),
        quantity=_positive_decimal(intent_payload.get("quantity"), "intent.quantity"),
        limit_price=_optional_positive_decimal(
            intent_payload.get("limit_price"),
            "intent.limit_price",
        ),
        strategy=_string(intent_payload.get("strategy"), "intent.strategy"),
        reason=_string(intent_payload.get("reason"), "intent.reason"),
    )
    state = ExecutionState(_required_str(payload.get("state"), "state"))
    correlation_id = _required_str(payload.get("correlation_id"), "correlation_id")
    execution_group_id = _optional_str(payload.get("execution_group_id"), "execution_group_id")
    execution_role = ExecutionRole(
        _required_str(payload.get("execution_role"), "execution_role")
    )
    events = [
        _deserialize_event(_mapping(item, "event"))
        for item in _list(payload.get("events"), "events")
    ]
    _validate_event_journal(
        execution_id,
        intent,
        state,
        correlation_id,
        execution_group_id,
        execution_role,
        events,
    )
    events_by_id = {event.event_id: event for event in events}
    if len(events_by_id) != len(events):
        raise InvalidCheckpointError("execution event ids must be unique")

    fills: dict[str, _FillRecord] = {}
    fill_notional = Decimal(0)
    filled_quantity = Decimal(0)
    for item in _list(payload.get("fills"), "fills"):
        fill_payload = _mapping(item, "fill")
        fill_id = _required_str(fill_payload.get("fill_id"), "fill.fill_id")
        if fill_id in fills:
            raise InvalidCheckpointError(f"duplicate fill_id: {fill_id}")
        quantity = _positive_decimal(fill_payload.get("quantity"), "fill.quantity")
        price = _positive_decimal(fill_payload.get("price"), "fill.price")
        event_id = _required_str(fill_payload.get("event_id"), "fill.event_id")
        event = events_by_id.get(event_id)
        if event is None:
            raise InvalidCheckpointError("fill references an unknown event")
        if (
            event.fill_id != fill_id
            or event.fill_quantity != quantity
            or event.fill_price != price
        ):
            raise InvalidCheckpointError("fill record does not match its execution event")
        fills[fill_id] = _FillRecord(quantity, price, event)
        filled_quantity += quantity
        fill_notional += quantity * price

    event_fill_ids = {event.fill_id for event in events if event.fill_id is not None}
    if event_fill_ids != set(fills):
        raise InvalidCheckpointError("fill events and fill accounting are inconsistent")
    _validate_fill_events(intent.quantity, events)
    _validate_fill_accounting(intent.quantity, state, filled_quantity)
    return execution_id, _ExecutionContext(
        intent=intent,
        state=state,
        correlation_id=correlation_id,
        execution_group_id=execution_group_id,
        execution_role=execution_role,
        events=events,
        fills=fills,
        filled_quantity=filled_quantity,
        fill_notional=fill_notional,
    )


def _serialize_event(event: ExecutionEvent) -> dict[str, object]:
    return {
        "event_id": event.event_id,
        "execution_id": event.execution_id,
        "state": event.state.value,
        "message": event.message,
        "timestamp": event.timestamp.isoformat(),
        "venue": event.venue.value if event.venue is not None else None,
        "symbol": event.symbol,
        "side": event.side.value if event.side is not None else None,
        "quantity": _string_decimal(event.quantity),
        "correlation_id": event.correlation_id,
        "execution_group_id": event.execution_group_id,
        "fill_id": event.fill_id,
        "fill_quantity": _string_decimal(event.fill_quantity),
        "fill_price": _string_decimal(event.fill_price),
        "cumulative_filled_quantity": _string_decimal(event.cumulative_filled_quantity),
        "remaining_quantity": _string_decimal(event.remaining_quantity),
        "average_fill_price": _string_decimal(event.average_fill_price),
        "execution_role": event.execution_role.value,
    }


def _deserialize_event(payload: Mapping[str, Any]) -> ExecutionEvent:
    venue = _optional_str(payload.get("venue"), "event.venue")
    side = _optional_str(payload.get("side"), "event.side")
    return ExecutionEvent(
        event_id=_required_str(payload.get("event_id"), "event.event_id"),
        execution_id=_required_str(payload.get("execution_id"), "event.execution_id"),
        state=ExecutionState(_required_str(payload.get("state"), "event.state")),
        message=_string(payload.get("message"), "event.message"),
        timestamp=_timestamp(payload.get("timestamp"), "event.timestamp"),
        venue=Venue(venue) if venue is not None else None,
        symbol=_optional_str(payload.get("symbol"), "event.symbol"),
        side=Side(side) if side is not None else None,
        quantity=_optional_decimal(payload.get("quantity"), "event.quantity"),
        correlation_id=_optional_str(
            payload.get("correlation_id"),
            "event.correlation_id",
        ),
        execution_group_id=_optional_str(
            payload.get("execution_group_id"),
            "event.execution_group_id",
        ),
        fill_id=_optional_str(payload.get("fill_id"), "event.fill_id"),
        fill_quantity=_optional_decimal(
            payload.get("fill_quantity"),
            "event.fill_quantity",
        ),
        fill_price=_optional_decimal(payload.get("fill_price"), "event.fill_price"),
        cumulative_filled_quantity=_optional_decimal(
            payload.get("cumulative_filled_quantity"),
            "event.cumulative_filled_quantity",
        ),
        remaining_quantity=_optional_decimal(
            payload.get("remaining_quantity"),
            "event.remaining_quantity",
        ),
        average_fill_price=_optional_decimal(
            payload.get("average_fill_price"),
            "event.average_fill_price",
        ),
        execution_role=ExecutionRole(
            _required_str(payload.get("execution_role"), "event.execution_role")
        ),
    )


def _validate_event_journal(
    execution_id: str,
    intent: OrderIntent,
    state: ExecutionState,
    correlation_id: str,
    execution_group_id: str | None,
    execution_role: ExecutionRole,
    events: list[ExecutionEvent],
) -> None:
    if not events:
        raise InvalidCheckpointError("execution event journal cannot be empty")
    if events[0].state not in {ExecutionState.SUBMITTED, ExecutionState.RISK_REJECTED}:
        raise InvalidCheckpointError("execution journal has an invalid initial state")
    previous = events[0]
    for index, event in enumerate(events):
        if (
            event.execution_id != execution_id
            or event.venue is not intent.venue
            or event.symbol != intent.symbol
            or event.side is not intent.side
            or event.quantity != intent.quantity
            or event.correlation_id != correlation_id
            or event.execution_group_id != execution_group_id
            or event.execution_role is not execution_role
        ):
            raise InvalidCheckpointError("execution event metadata is inconsistent")
        if index > 0:
            if event.state not in ExecutionOrchestrator._ALLOWED_TRANSITIONS[previous.state]:
                raise InvalidCheckpointError("execution journal contains an invalid transition")
            if event.timestamp < previous.timestamp:
                raise InvalidCheckpointError("execution event timestamps are not monotonic")
        previous = event
    if events[-1].state is not state:
        raise InvalidCheckpointError("execution state does not match its last event")


def _validate_fill_accounting(
    requested_quantity: Decimal,
    state: ExecutionState,
    filled_quantity: Decimal,
) -> None:
    if filled_quantity > requested_quantity:
        raise InvalidCheckpointError("checkpoint contains an execution overfill")
    if state is ExecutionState.PARTIALLY_FILLED and not 0 < filled_quantity < requested_quantity:
        raise InvalidCheckpointError("partial-fill state has inconsistent fill accounting")
    if state is ExecutionState.FILLED and filled_quantity != requested_quantity:
        raise InvalidCheckpointError("filled state has inconsistent fill accounting")
    if state in {ExecutionState.SUBMITTED, ExecutionState.RISK_REJECTED} and filled_quantity != 0:
        raise InvalidCheckpointError("unfilled execution state contains fills")
    if state in {ExecutionState.CANCELED, ExecutionState.EXPIRED} and filled_quantity >= requested_quantity:
        raise InvalidCheckpointError("closed order cannot contain a complete fill")


def _validate_fill_events(
    requested_quantity: Decimal,
    events: list[ExecutionEvent],
) -> None:
    cumulative_quantity = Decimal(0)
    cumulative_notional = Decimal(0)
    for event in events:
        if event.fill_id is None:
            if any(
                value is not None
                for value in (
                    event.fill_quantity,
                    event.fill_price,
                    event.cumulative_filled_quantity,
                    event.remaining_quantity,
                    event.average_fill_price,
                )
            ):
                raise InvalidCheckpointError("non-fill event contains fill accounting")
            continue
        if event.fill_quantity is None or event.fill_price is None:
            raise InvalidCheckpointError("fill event is missing quantity or price")
        cumulative_quantity += event.fill_quantity
        cumulative_notional += event.fill_quantity * event.fill_price
        remaining_quantity = requested_quantity - cumulative_quantity
        expected_state = (
            ExecutionState.FILLED
            if remaining_quantity == 0
            else ExecutionState.PARTIALLY_FILLED
        )
        if (
            cumulative_quantity > requested_quantity
            or event.state is not expected_state
            or event.cumulative_filled_quantity != cumulative_quantity
            or event.remaining_quantity != remaining_quantity
            or event.average_fill_price != cumulative_notional / cumulative_quantity
        ):
            raise InvalidCheckpointError("fill event cumulative accounting is inconsistent")


def _serialize_reconciliation(reconciliation: GroupReconciliation) -> dict[str, object]:
    residual = reconciliation.residual
    return {
        "execution_group_id": reconciliation.execution_group_id,
        "state": reconciliation.state.value,
        "buy_execution_id": reconciliation.buy_execution_id,
        "sell_execution_id": reconciliation.sell_execution_id,
        "target_quantity": str(reconciliation.target_quantity),
        "buy_filled_quantity": str(reconciliation.buy_filled_quantity),
        "sell_filled_quantity": str(reconciliation.sell_filled_quantity),
        "matched_quantity": str(reconciliation.matched_quantity),
        "residual": (
            {
                "symbol": residual.symbol,
                "signed_quantity": str(residual.signed_quantity),
                "hedge_side": residual.hedge_side.value,
                "hedge_quantity": str(residual.hedge_quantity),
            }
            if residual is not None
            else None
        ),
        "hedge_execution_id": reconciliation.hedge_execution_id,
        "post_hedge_residual_quantity": str(
            reconciliation.post_hedge_residual_quantity
        ),
        "message": reconciliation.message,
    }


def _deserialize_reconciliation(payload: Mapping[str, Any]) -> GroupReconciliation:
    residual_payload = payload.get("residual")
    residual = None
    if residual_payload is not None:
        residual_data = _mapping(residual_payload, "reconciliation.residual")
        signed_quantity = _decimal(
            residual_data.get("signed_quantity"),
            "reconciliation.residual.signed_quantity",
        )
        hedge_quantity = _positive_decimal(
            residual_data.get("hedge_quantity"),
            "reconciliation.residual.hedge_quantity",
        )
        hedge_side = Side(
            _required_str(
                residual_data.get("hedge_side"),
                "reconciliation.residual.hedge_side",
            )
        )
        if signed_quantity == 0 or hedge_quantity != abs(signed_quantity):
            raise InvalidCheckpointError("residual quantities are inconsistent")
        if hedge_side is not (Side.SELL if signed_quantity > 0 else Side.BUY):
            raise InvalidCheckpointError("residual hedge side is inconsistent")
        residual = ResidualExposure(
            symbol=_required_str(
                residual_data.get("symbol"),
                "reconciliation.residual.symbol",
            ),
            signed_quantity=signed_quantity,
            hedge_side=hedge_side,
            hedge_quantity=hedge_quantity,
        )
    return GroupReconciliation(
        execution_group_id=_required_str(
            payload.get("execution_group_id"),
            "reconciliation.execution_group_id",
        ),
        state=GroupReconciliationState(
            _required_str(payload.get("state"), "reconciliation.state")
        ),
        buy_execution_id=_required_str(
            payload.get("buy_execution_id"),
            "reconciliation.buy_execution_id",
        ),
        sell_execution_id=_required_str(
            payload.get("sell_execution_id"),
            "reconciliation.sell_execution_id",
        ),
        target_quantity=_positive_decimal(
            payload.get("target_quantity"),
            "reconciliation.target_quantity",
        ),
        buy_filled_quantity=_non_negative_decimal(
            payload.get("buy_filled_quantity"),
            "reconciliation.buy_filled_quantity",
        ),
        sell_filled_quantity=_non_negative_decimal(
            payload.get("sell_filled_quantity"),
            "reconciliation.sell_filled_quantity",
        ),
        matched_quantity=_non_negative_decimal(
            payload.get("matched_quantity"),
            "reconciliation.matched_quantity",
        ),
        residual=residual,
        hedge_execution_id=_optional_str(
            payload.get("hedge_execution_id"),
            "reconciliation.hedge_execution_id",
        ),
        post_hedge_residual_quantity=_decimal(
            payload.get("post_hedge_residual_quantity"),
            "reconciliation.post_hedge_residual_quantity",
        ),
        message=_required_str(payload.get("message"), "reconciliation.message"),
    )


def _validate_reconciliation(
    orchestrator: ExecutionOrchestrator,
    reconciliation: GroupReconciliation,
) -> None:
    execution_ids = orchestrator._group_legs.get(reconciliation.execution_group_id)
    if execution_ids is None or len(execution_ids) != 2:
        raise InvalidCheckpointError("reconciliation requires exactly two primary legs")
    if set(execution_ids) != {
        reconciliation.buy_execution_id,
        reconciliation.sell_execution_id,
    }:
        raise InvalidCheckpointError("reconciliation leg references are inconsistent")
    buy = orchestrator._executions[reconciliation.buy_execution_id]
    sell = orchestrator._executions[reconciliation.sell_execution_id]
    if buy.intent.side is not Side.BUY or sell.intent.side is not Side.SELL:
        raise InvalidCheckpointError("reconciliation leg sides are inconsistent")
    if (
        reconciliation.target_quantity != buy.intent.quantity
        or reconciliation.buy_filled_quantity != buy.filled_quantity
        or reconciliation.sell_filled_quantity != sell.filled_quantity
        or reconciliation.matched_quantity != min(buy.filled_quantity, sell.filled_quantity)
    ):
        raise InvalidCheckpointError("reconciliation quantities are inconsistent")
    signed_residual = buy.filled_quantity - sell.filled_quantity
    if reconciliation.residual is not None and (
        reconciliation.residual.symbol != buy.intent.symbol
        or reconciliation.residual.signed_quantity != signed_residual
    ):
        raise InvalidCheckpointError("reconciliation residual is inconsistent")

    expected_primary_state = {
        GroupReconciliationState.BALANCED: ExecutionState.COMPLETED,
        GroupReconciliationState.HEDGE_REQUIRED: ExecutionState.HEDGE_REQUIRED,
        GroupReconciliationState.HEDGED: ExecutionState.COMPLETED,
        GroupReconciliationState.HALTED: ExecutionState.HALTED,
    }[reconciliation.state]
    if buy.state is not expected_primary_state or sell.state is not expected_primary_state:
        raise InvalidCheckpointError("reconciliation state does not match its primary legs")
    if reconciliation.state is GroupReconciliationState.BALANCED:
        if reconciliation.residual is not None or reconciliation.hedge_execution_id is not None:
            raise InvalidCheckpointError("balanced reconciliation contains hedge metadata")
    else:
        if reconciliation.residual is None:
            raise InvalidCheckpointError("unbalanced reconciliation has no residual")
    if reconciliation.state is GroupReconciliationState.HEDGE_REQUIRED and (
        reconciliation.hedge_execution_id is not None
        or reconciliation.post_hedge_residual_quantity != signed_residual
    ):
        raise InvalidCheckpointError("pending residual hedge metadata is inconsistent")
    if reconciliation.state is GroupReconciliationState.HEDGED:
        residual = reconciliation.residual
        if residual is None:
            raise InvalidCheckpointError("completed hedge has no residual metadata")
        hedge_execution_id = reconciliation.hedge_execution_id
        hedge = orchestrator._executions.get(hedge_execution_id or "")
        if (
            hedge is None
            or hedge.execution_role is not ExecutionRole.RESIDUAL_HEDGE
            or hedge.execution_group_id != reconciliation.execution_group_id
            or hedge.state is not ExecutionState.COMPLETED
            or hedge.intent.symbol != residual.symbol
            or hedge.intent.side is not residual.hedge_side
            or hedge.intent.quantity != residual.hedge_quantity
            or hedge.filled_quantity != residual.hedge_quantity
            or reconciliation.post_hedge_residual_quantity != 0
        ):
            raise InvalidCheckpointError("completed residual hedge metadata is inconsistent")
    if (
        reconciliation.state is GroupReconciliationState.HALTED
        and (
            reconciliation.hedge_execution_id is not None
            or reconciliation.post_hedge_residual_quantity != signed_residual
        )
    ):
        raise InvalidCheckpointError("halted reconciliation metadata is inconsistent")


def _mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise InvalidCheckpointError(f"{field_name} must be an object")
    return value


def _list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise InvalidCheckpointError(f"{field_name} must be an array")
    return value


def _required_str(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise InvalidCheckpointError(f"{field_name} must be a non-empty string")
    return value


def _string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise InvalidCheckpointError(f"{field_name} must be a string")
    return value


def _optional_str(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise InvalidCheckpointError(f"{field_name} must be null or a non-empty string")
    return value


def _decimal(value: object, field_name: str) -> Decimal:
    number = Decimal(str(value))
    if not number.is_finite():
        raise InvalidCheckpointError(f"{field_name} must be finite")
    return number


def _positive_decimal(value: object, field_name: str) -> Decimal:
    number = _decimal(value, field_name)
    if number <= 0:
        raise InvalidCheckpointError(f"{field_name} must be positive")
    return number


def _non_negative_decimal(value: object, field_name: str) -> Decimal:
    number = _decimal(value, field_name)
    if number < 0:
        raise InvalidCheckpointError(f"{field_name} cannot be negative")
    return number


def _optional_decimal(value: object, field_name: str) -> Decimal | None:
    return None if value is None else _decimal(value, field_name)


def _optional_positive_decimal(value: object, field_name: str) -> Decimal | None:
    return None if value is None else _positive_decimal(value, field_name)


def _string_decimal(value: Decimal | None) -> str | None:
    return str(value) if value is not None else None


def _timestamp(value: object, field_name: str) -> datetime:
    timestamp = datetime.fromisoformat(_required_str(value, field_name))
    if timestamp.tzinfo is None:
        raise InvalidCheckpointError(f"{field_name} must include a timezone")
    return timestamp
