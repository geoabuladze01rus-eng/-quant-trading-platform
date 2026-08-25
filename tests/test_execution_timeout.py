from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from quant_platform.domain import OrderIntent, Side, Venue
from quant_platform.execution import PaperExecutionEngine
from quant_platform.execution_checkpoint import JsonExecutionCheckpointStore
from quant_platform.execution_orchestrator import (
    ExecutionState,
    GroupReconciliationState,
)
from quant_platform.execution_timeout import ExecutionTimeoutController
from quant_platform.risk import RiskDecision


def intent(venue: Venue, side: Side) -> OrderIntent:
    return OrderIntent(
        venue=venue,
        symbol="BTCUSDT",
        side=side,
        quantity=Decimal("0.01"),
        limit_price=Decimal(100000),
        strategy="arbitrage",
        reason="timeout test",
    )


def submit_group(engine: PaperExecutionEngine) -> tuple[str, str]:
    risk = RiskDecision(True, "ok")
    buy = engine.submit(
        intent(Venue.BINANCE, Side.BUY),
        risk,
        execution_group_id="group-1",
    )
    sell = engine.submit(
        intent(Venue.BYBIT, Side.SELL),
        risk,
        execution_group_id="group-1",
    )
    return buy["execution_id"], sell["execution_id"]


def deadline(engine: PaperExecutionEngine, *, seconds: int = 6):
    return engine.orchestrator.group_snapshots()[0].submitted_at + timedelta(
        seconds=seconds
    )


def test_sweep_leaves_group_open_before_deadline() -> None:
    engine = PaperExecutionEngine()
    buy_id, sell_id = submit_group(engine)
    controller = ExecutionTimeoutController(engine, timedelta(seconds=5))

    results = controller.sweep(now=deadline(engine, seconds=4))

    assert results == ()
    assert engine.orchestrator.current_state(buy_id) is ExecutionState.SUBMITTED
    assert engine.orchestrator.current_state(sell_id) is ExecutionState.SUBMITTED


def test_sweep_expires_and_balances_two_unfilled_legs() -> None:
    engine = PaperExecutionEngine()
    buy_id, sell_id = submit_group(engine)
    controller = ExecutionTimeoutController(engine, timedelta(seconds=5))

    (result,) = controller.sweep(now=deadline(engine))

    assert set(result.expired_execution_ids) == {buy_id, sell_id}
    assert result.reconciliation is not None
    assert result.reconciliation.state is GroupReconciliationState.BALANCED
    assert result.reconciliation.matched_quantity == 0
    assert result.resulting_states == (
        ExecutionState.COMPLETED,
        ExecutionState.COMPLETED,
    )
    assert controller.sweep(now=deadline(engine, seconds=10)) == ()


def test_sweep_expires_orphaned_first_leg_without_reconciliation() -> None:
    engine = PaperExecutionEngine()
    result = engine.submit(
        intent(Venue.BINANCE, Side.BUY),
        RiskDecision(True, "ok"),
        execution_group_id="orphaned-group",
    )
    execution_id = result["execution_id"]
    controller = ExecutionTimeoutController(engine, timedelta(seconds=5))

    (sweep_result,) = controller.sweep(now=deadline(engine))

    assert sweep_result.expired_execution_ids == (execution_id,)
    assert sweep_result.reconciliation is None
    assert sweep_result.resulting_states == (ExecutionState.EXPIRED,)
    assert controller.sweep(now=deadline(engine, seconds=10)) == ()


def test_sweep_detects_residual_after_asymmetric_fill() -> None:
    engine = PaperExecutionEngine()
    buy_id, sell_id = submit_group(engine)
    engine.process_fill(
        buy_id,
        fill_id="buy-fill",
        quantity=Decimal("0.01"),
        price=Decimal(99990),
    )
    engine.process_fill(
        sell_id,
        fill_id="sell-fill",
        quantity=Decimal("0.004"),
        price=Decimal(100100),
    )
    controller = ExecutionTimeoutController(engine, timedelta(seconds=5))

    (result,) = controller.sweep(now=deadline(engine))

    assert result.expired_execution_ids == (sell_id,)
    assert result.reconciliation is not None
    assert result.reconciliation.state is GroupReconciliationState.HEDGE_REQUIRED
    assert result.reconciliation.residual is not None
    assert result.reconciliation.residual.signed_quantity == Decimal("0.006")
    assert result.reconciliation.residual.hedge_side is Side.SELL
    assert result.resulting_states == (
        ExecutionState.HEDGE_REQUIRED,
        ExecutionState.HEDGE_REQUIRED,
    )


def test_recovered_controller_finishes_pending_group(tmp_path: Path) -> None:
    store = JsonExecutionCheckpointStore(tmp_path / "execution.json")
    engine = PaperExecutionEngine(checkpoint_store=store)
    buy_id, sell_id = submit_group(engine)
    engine.process_fill(
        buy_id,
        fill_id="buy-fill",
        quantity=Decimal("0.004"),
        price=Decimal(99990),
    )
    checked_at = deadline(engine)

    recovered = PaperExecutionEngine.from_checkpoint_store(store)
    controller = ExecutionTimeoutController(recovered, timedelta(seconds=5))
    (result,) = controller.sweep(now=checked_at)
    persisted = PaperExecutionEngine.from_checkpoint_store(store)

    assert set(result.expired_execution_ids) == {buy_id, sell_id}
    assert result.reconciliation is not None
    assert result.reconciliation.state is GroupReconciliationState.HEDGE_REQUIRED
    assert persisted.reconcile_group("group-1") == result.reconciliation


def test_sweep_requires_timezone_aware_timestamp() -> None:
    engine = PaperExecutionEngine()
    submit_group(engine)
    controller = ExecutionTimeoutController(engine)
    naive = engine.orchestrator.group_snapshots()[0].submitted_at.replace(tzinfo=None)

    with pytest.raises(ValueError, match="timezone-aware"):
        controller.sweep(now=naive)


def test_timeout_must_be_positive() -> None:
    with pytest.raises(ValueError, match="must be positive"):
        ExecutionTimeoutController(PaperExecutionEngine(), timedelta(0))
