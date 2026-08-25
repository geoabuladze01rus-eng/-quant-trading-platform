import json
import stat
from decimal import Decimal
from pathlib import Path

import pytest

from quant_platform.domain import OrderIntent, Side, Venue
from quant_platform.execution import PaperExecutionEngine
from quant_platform.execution_checkpoint import JsonExecutionCheckpointStore
from quant_platform.execution_orchestrator import (
    ExecutionRole,
    ExecutionState,
    GroupReconciliationState,
    InvalidCheckpointError,
    OrderCloseReason,
)
from quant_platform.risk import RiskDecision


def intent(venue: Venue, side: Side) -> OrderIntent:
    return OrderIntent(
        venue=venue,
        symbol="BTCUSDT",
        side=side,
        quantity=Decimal("0.01"),
        limit_price=Decimal(100000),
        strategy="arbitrage",
        reason="recovery test",
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


def round_trip(engine: PaperExecutionEngine) -> PaperExecutionEngine:
    serialized = json.dumps(engine.export_checkpoint())
    return PaperExecutionEngine.from_checkpoint(json.loads(serialized))


def test_checkpoint_round_trip_preserves_partial_fill_idempotency() -> None:
    engine = PaperExecutionEngine()
    buy_id, sell_id = submit_group(engine)
    original = engine.process_fill(
        buy_id,
        fill_id="buy-fill-1",
        quantity=Decimal("0.004"),
        price=Decimal(99990),
    )
    engine.process_fill(
        sell_id,
        fill_id="sell-fill-1",
        quantity=Decimal("0.004"),
        price=Decimal(100100),
    )

    recovered = round_trip(engine)
    duplicate = recovered.process_fill(
        buy_id,
        fill_id="buy-fill-1",
        quantity=Decimal("0.004"),
        price=Decimal(99990),
    )

    assert duplicate["event_id"] == original["event_id"]
    assert recovered.orchestrator.snapshot(buy_id).filled_quantity == Decimal("0.004")
    recovered.close_order(buy_id, OrderCloseReason.CANCELED)
    recovered.close_order(sell_id, OrderCloseReason.EXPIRED)
    result = recovered.reconcile_group("group-1")
    assert result.state is GroupReconciliationState.BALANCED
    assert result.matched_quantity == Decimal("0.004")


def test_recovery_resumes_pending_residual_hedge() -> None:
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
        quantity=Decimal("0.006"),
        price=Decimal(100100),
    )
    engine.close_order(sell_id, OrderCloseReason.CANCELED)
    before_restart = engine.reconcile_group("group-1")
    assert before_restart.state is GroupReconciliationState.HEDGE_REQUIRED

    recovered = round_trip(engine)
    restored_reconciliation = recovered.reconcile_group("group-1")
    result = recovered.hedge_residual(
        "group-1",
        venue=Venue.BINANCE,
        fill_id="recovery-hedge-fill",
        price=Decimal(100010),
        reference_price=Decimal(100000),
    )

    assert restored_reconciliation == before_restart
    assert result.state is GroupReconciliationState.HEDGED
    assert result.hedge_execution_id is not None
    assert result.post_hedge_residual_quantity == 0
    hedge = recovered.orchestrator.snapshot(result.hedge_execution_id)
    assert hedge.execution_role is ExecutionRole.RESIDUAL_HEDGE
    assert hedge.state is ExecutionState.COMPLETED
    assert recovered.orchestrator.current_state(buy_id) is ExecutionState.COMPLETED
    assert recovered.orchestrator.current_state(sell_id) is ExecutionState.COMPLETED


def test_completed_hedge_remains_idempotent_after_second_restart() -> None:
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
        quantity=Decimal("0.006"),
        price=Decimal(100100),
    )
    engine.close_order(sell_id, OrderCloseReason.CANCELED)
    engine.reconcile_group("group-1")
    completed = engine.hedge_residual(
        "group-1",
        venue=Venue.BINANCE,
        fill_id="hedge-fill",
        price=Decimal(100010),
        reference_price=Decimal(100000),
    )

    recovered = round_trip(engine)
    repeated = recovered.hedge_residual(
        "group-1",
        venue=Venue.BINANCE,
        fill_id="ignored-after-terminal",
        price=Decimal(1),
        reference_price=Decimal(1),
    )

    assert repeated == completed
    assert repeated.hedge_execution_id is not None
    assert len(recovered.orchestrator.events(repeated.hedge_execution_id)) == 4


def test_corrupted_fill_checkpoint_is_rejected_atomically() -> None:
    engine = PaperExecutionEngine()
    buy_id, _ = submit_group(engine)
    engine.process_fill(
        buy_id,
        fill_id="buy-fill",
        quantity=Decimal("0.004"),
        price=Decimal(99990),
    )
    checkpoint = json.loads(json.dumps(engine.export_checkpoint()))
    buy_execution = next(
        item for item in checkpoint["executions"] if item["execution_id"] == buy_id
    )
    buy_execution["fills"][0]["quantity"] = "0.009"

    with pytest.raises(InvalidCheckpointError, match="fill record"):
        PaperExecutionEngine.from_checkpoint(checkpoint)


def test_invalid_journal_and_schema_are_rejected() -> None:
    engine = PaperExecutionEngine()
    submit_group(engine)
    checkpoint = json.loads(json.dumps(engine.export_checkpoint()))
    checkpoint["executions"][0]["state"] = ExecutionState.COMPLETED.value

    with pytest.raises(InvalidCheckpointError, match="last event"):
        PaperExecutionEngine.from_checkpoint(checkpoint)

    checkpoint = engine.export_checkpoint()
    checkpoint["schema_version"] = 999
    with pytest.raises(InvalidCheckpointError, match="unsupported checkpoint"):
        PaperExecutionEngine.from_checkpoint(checkpoint)


def test_corrupted_cumulative_fill_audit_fields_are_rejected() -> None:
    engine = PaperExecutionEngine()
    buy_id, _ = submit_group(engine)
    engine.process_fill(
        buy_id,
        fill_id="buy-fill",
        quantity=Decimal("0.004"),
        price=Decimal(99990),
    )
    checkpoint = json.loads(json.dumps(engine.export_checkpoint()))
    buy_execution = next(
        item for item in checkpoint["executions"] if item["execution_id"] == buy_id
    )
    fill_event = next(event for event in buy_execution["events"] if event["fill_id"])
    fill_event["cumulative_filled_quantity"] = "0.003"

    with pytest.raises(InvalidCheckpointError, match="cumulative accounting"):
        PaperExecutionEngine.from_checkpoint(checkpoint)


@pytest.mark.parametrize(
    ("notional", "slippage"),
    [
        (Decimal(0), Decimal(30)),
        (Decimal(10000), Decimal("-0.1")),
    ],
)
def test_recovered_engine_rejects_unsafe_hedge_limits(
    notional: Decimal,
    slippage: Decimal,
) -> None:
    engine = PaperExecutionEngine()

    with pytest.raises(ValueError, match="max residual hedge"):
        PaperExecutionEngine.from_checkpoint(
            engine.export_checkpoint(),
            max_residual_hedge_notional=notional,
            max_residual_hedge_slippage_bps=slippage,
        )


def test_atomic_file_store_persists_and_recovers_checkpoint(tmp_path: Path) -> None:
    engine = PaperExecutionEngine()
    buy_id, _ = submit_group(engine)
    engine.process_fill(
        buy_id,
        fill_id="buy-fill",
        quantity=Decimal("0.004"),
        price=Decimal(99990),
    )
    store = JsonExecutionCheckpointStore(tmp_path / "runtime" / "execution.json")

    engine.save_checkpoint(store)
    recovered = PaperExecutionEngine.from_checkpoint_store(store)

    assert recovered.orchestrator.snapshot(buy_id).filled_quantity == Decimal("0.004")
    assert stat.S_IMODE(store.path.stat().st_mode) == 0o600
    assert list(store.path.parent.glob("*.tmp")) == []


def test_checkpoint_store_tracks_every_execution_mutation(tmp_path: Path) -> None:
    store = JsonExecutionCheckpointStore(tmp_path / "runtime" / "execution.json")
    engine = PaperExecutionEngine(checkpoint_store=store)

    buy_id, sell_id = submit_group(engine)
    submitted = PaperExecutionEngine.from_checkpoint_store(store)
    assert submitted.orchestrator.current_state(buy_id) is ExecutionState.SUBMITTED
    assert submitted.orchestrator.current_state(sell_id) is ExecutionState.SUBMITTED

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
    engine.close_order(sell_id, OrderCloseReason.EXPIRED)
    reconciled = engine.reconcile_group("group-1")

    pending_hedge = PaperExecutionEngine.from_checkpoint_store(store)
    assert reconciled.state is GroupReconciliationState.HEDGE_REQUIRED
    assert (
        pending_hedge.reconcile_group("group-1").state
        is GroupReconciliationState.HEDGE_REQUIRED
    )

    engine.hedge_residual(
        "group-1",
        venue=Venue.BINANCE,
        fill_id="hedge-fill",
        price=Decimal(100010),
        reference_price=Decimal(100000),
    )
    completed = PaperExecutionEngine.from_checkpoint_store(store)

    result = completed.reconcile_group("group-1")
    assert result.state is GroupReconciliationState.HEDGED
    assert result.post_hedge_residual_quantity == 0


def test_recovered_store_continues_automatic_checkpointing(tmp_path: Path) -> None:
    store = JsonExecutionCheckpointStore(tmp_path / "execution.json")
    engine = PaperExecutionEngine(checkpoint_store=store)
    buy_id, _ = submit_group(engine)

    recovered = PaperExecutionEngine.from_checkpoint_store(store)
    recovered.process_fill(
        buy_id,
        fill_id="fill-after-restart",
        quantity=Decimal("0.004"),
        price=Decimal(99990),
    )

    second_recovery = PaperExecutionEngine.from_checkpoint_store(store)
    assert second_recovery.orchestrator.snapshot(buy_id).filled_quantity == Decimal(
        "0.004"
    )


def test_file_store_rejects_invalid_json(tmp_path: Path) -> None:
    store = JsonExecutionCheckpointStore(tmp_path / "execution.json")
    store.path.write_text("not-json", encoding="utf-8")

    with pytest.raises(InvalidCheckpointError, match="cannot read"):
        PaperExecutionEngine.from_checkpoint_store(store)
