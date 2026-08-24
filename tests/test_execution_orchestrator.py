from decimal import Decimal

import pytest

from quant_platform.domain import OrderIntent, Side, Venue
from quant_platform.execution_orchestrator import (
    ExecutionOrchestrator,
    ExecutionState,
    InvalidExecutionTransition,
    UnknownExecutionError,
)
from quant_platform.risk import RiskDecision


def intent() -> OrderIntent:
    return OrderIntent(
        Venue.BINANCE,
        "BTCUSDT",
        Side.BUY,
        Decimal("0.01"),
        None,
        "arb",
        "test",
    )


def test_rejected_execution_stops_before_submit() -> None:
    orchestrator = ExecutionOrchestrator()
    execution_id, events = orchestrator.start(
        intent(),
        RiskDecision(False, "daily loss"),
    )

    assert execution_id
    assert events[0].state is ExecutionState.RISK_REJECTED
    assert orchestrator.current_state(execution_id) is ExecutionState.RISK_REJECTED
    with pytest.raises(InvalidExecutionTransition, match="risk_rejected -> submitted"):
        orchestrator.transition(execution_id, ExecutionState.SUBMITTED, "retry")


def test_approved_execution_enters_submitted_with_audit_metadata() -> None:
    orchestrator = ExecutionOrchestrator()
    execution_id, events = orchestrator.start(
        intent(),
        RiskDecision(True, "ok"),
        correlation_id="corr-1",
        execution_group_id="group-1",
    )

    event = events[0]
    assert execution_id
    assert event.state is ExecutionState.SUBMITTED
    assert event.timestamp.tzinfo is not None
    assert event.venue is Venue.BINANCE
    assert event.symbol == "BTCUSDT"
    assert event.side is Side.BUY
    assert event.quantity == Decimal("0.01")
    assert event.correlation_id == "corr-1"
    assert event.execution_group_id == "group-1"


def test_lifecycle_accepts_only_contiguous_transitions() -> None:
    orchestrator = ExecutionOrchestrator()
    execution_id, _ = orchestrator.start(intent(), RiskDecision(True, "ok"))

    partial = orchestrator.transition(
        execution_id,
        ExecutionState.PARTIALLY_FILLED,
        "partial",
    )
    filled = orchestrator.transition(execution_id, ExecutionState.FILLED, "filled")
    reconciling = orchestrator.transition(
        execution_id,
        ExecutionState.RECONCILING,
        "reconciling",
    )
    completed = orchestrator.transition(
        execution_id,
        ExecutionState.COMPLETED,
        "balanced",
    )

    assert partial.execution_id == execution_id
    assert filled.execution_id == execution_id
    assert reconciling.execution_id == execution_id
    assert completed.execution_id == execution_id
    assert orchestrator.current_state(execution_id) is ExecutionState.COMPLETED
    assert [event.state for event in orchestrator.events(execution_id)] == [
        ExecutionState.SUBMITTED,
        ExecutionState.PARTIALLY_FILLED,
        ExecutionState.FILLED,
        ExecutionState.RECONCILING,
        ExecutionState.COMPLETED,
    ]


def test_lifecycle_rejects_skipped_and_terminal_transitions() -> None:
    orchestrator = ExecutionOrchestrator()
    execution_id, _ = orchestrator.start(intent(), RiskDecision(True, "ok"))

    with pytest.raises(InvalidExecutionTransition, match="submitted -> completed"):
        orchestrator.transition(execution_id, ExecutionState.COMPLETED, "skip")

    orchestrator.transition(execution_id, ExecutionState.FILLED, "filled")
    orchestrator.transition(execution_id, ExecutionState.COMPLETED, "done")
    with pytest.raises(InvalidExecutionTransition, match="completed -> halted"):
        orchestrator.transition(execution_id, ExecutionState.HALTED, "too late")


def test_unknown_execution_is_rejected() -> None:
    with pytest.raises(UnknownExecutionError):
        ExecutionOrchestrator().transition(
            "missing",
            ExecutionState.FILLED,
            "filled",
        )
