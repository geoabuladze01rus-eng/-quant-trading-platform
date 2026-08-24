from decimal import Decimal

import pytest

from quant_platform.domain import OrderIntent, Side, Venue
from quant_platform.execution import PaperExecutionEngine
from quant_platform.execution_orchestrator import (
    ConflictingFillError,
    ExecutionOrchestrator,
    ExecutionState,
    InvalidExecutionTransition,
    InvalidFillError,
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


def test_paper_execution_uses_canonical_lifecycle_and_preserves_status() -> None:
    engine = PaperExecutionEngine()

    result = engine.submit(
        intent(),
        RiskDecision(True, "ok"),
        correlation_id="corr-1",
        execution_group_id="group-1",
    )

    assert result["status"] == "paper_accepted"
    assert result["state"] == ExecutionState.SUBMITTED.value
    assert result["correlation_id"] == "corr-1"
    assert result["execution_group_id"] == "group-1"
    assert (
        engine.orchestrator.current_state(result["execution_id"])
        is ExecutionState.SUBMITTED
    )


def test_paper_execution_records_risk_rejection_in_canonical_lifecycle() -> None:
    engine = PaperExecutionEngine()

    result = engine.submit(intent(), RiskDecision(False, "daily loss"))

    assert result["status"] == "rejected"
    assert result["reason"] == "daily loss"
    assert result["state"] == ExecutionState.RISK_REJECTED.value
    assert (
        engine.orchestrator.current_state(result["execution_id"])
        is ExecutionState.RISK_REJECTED
    )


def test_incremental_fills_advance_lifecycle_and_calculate_weighted_price() -> None:
    orchestrator = ExecutionOrchestrator()
    execution_id, _ = orchestrator.start(intent(), RiskDecision(True, "ok"))

    first = orchestrator.process_fill(
        execution_id,
        fill_id="fill-1",
        quantity=Decimal("0.004"),
        price=Decimal(100000),
    )
    second = orchestrator.process_fill(
        execution_id,
        fill_id="fill-2",
        quantity=Decimal("0.006"),
        price=Decimal(100100),
    )

    assert first.state is ExecutionState.PARTIALLY_FILLED
    assert first.cumulative_filled_quantity == Decimal("0.004")
    assert first.remaining_quantity == Decimal("0.006")
    assert second.state is ExecutionState.FILLED
    assert second.cumulative_filled_quantity == Decimal("0.010")
    assert second.remaining_quantity == 0
    snapshot = orchestrator.snapshot(execution_id)
    assert snapshot.filled_quantity == Decimal("0.010")
    assert snapshot.average_fill_price == Decimal(100060)


def test_duplicate_fill_is_idempotent_but_conflicting_payload_is_rejected() -> None:
    orchestrator = ExecutionOrchestrator()
    execution_id, _ = orchestrator.start(intent(), RiskDecision(True, "ok"))
    original = orchestrator.process_fill(
        execution_id,
        fill_id="fill-1",
        quantity=Decimal("0.004"),
        price=Decimal(100000),
    )

    duplicate = orchestrator.process_fill(
        execution_id,
        fill_id="fill-1",
        quantity=Decimal("0.004"),
        price=Decimal(100000),
    )

    assert duplicate is original
    assert len(orchestrator.events(execution_id)) == 2
    with pytest.raises(ConflictingFillError, match="different values"):
        orchestrator.process_fill(
            execution_id,
            fill_id="fill-1",
            quantity=Decimal("0.005"),
            price=Decimal(100000),
        )


def test_overfill_and_late_fill_are_rejected_without_mutating_accounting() -> None:
    orchestrator = ExecutionOrchestrator()
    execution_id, _ = orchestrator.start(intent(), RiskDecision(True, "ok"))

    with pytest.raises(InvalidFillError, match="exceeds requested"):
        orchestrator.process_fill(
            execution_id,
            fill_id="overfill",
            quantity=Decimal("0.011"),
            price=Decimal(100000),
        )
    assert orchestrator.snapshot(execution_id).filled_quantity == 0

    orchestrator.process_fill(
        execution_id,
        fill_id="fill-1",
        quantity=Decimal("0.01"),
        price=Decimal(100000),
    )
    with pytest.raises(InvalidExecutionTransition, match="execution is filled"):
        orchestrator.process_fill(
            execution_id,
            fill_id="late-fill",
            quantity=Decimal("0.001"),
            price=Decimal(100000),
        )


def test_paper_execution_exposes_fill_processing_without_live_calls() -> None:
    engine = PaperExecutionEngine()
    submitted = engine.submit(intent(), RiskDecision(True, "ok"))

    result = engine.process_fill(
        submitted["execution_id"],
        fill_id="fill-1",
        quantity=Decimal("0.004"),
        price=Decimal(100000),
    )

    assert result["state"] == ExecutionState.PARTIALLY_FILLED.value
    assert result["cumulative_filled_quantity"] == "0.004"
    assert result["remaining_quantity"] == "0.006"
