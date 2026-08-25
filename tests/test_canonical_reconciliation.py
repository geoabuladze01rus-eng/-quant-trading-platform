from decimal import Decimal

import pytest

from quant_platform.domain import OrderIntent, Side, Venue
from quant_platform.execution import PaperExecutionEngine
from quant_platform.execution_orchestrator import (
    ExecutionRole,
    ExecutionState,
    GroupReconciliationState,
    InvalidExecutionGroupError,
    InvalidExecutionTransition,
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
        reason="test",
    )


def submit_group(engine: PaperExecutionEngine, group_id: str = "group-1") -> tuple[str, str]:
    risk = RiskDecision(True, "ok")
    buy = engine.submit(
        intent(Venue.BINANCE, Side.BUY),
        risk,
        execution_group_id=group_id,
    )
    sell = engine.submit(
        intent(Venue.BYBIT, Side.SELL),
        risk,
        execution_group_id=group_id,
    )
    return buy["execution_id"], sell["execution_id"]


def fill(
    engine: PaperExecutionEngine,
    execution_id: str,
    fill_id: str,
    quantity: str,
    price: int = 100000,
) -> None:
    engine.process_fill(
        execution_id,
        fill_id=fill_id,
        quantity=Decimal(quantity),
        price=Decimal(price),
    )


def close(
    engine: PaperExecutionEngine,
    execution_id: str,
    reason: OrderCloseReason = OrderCloseReason.CANCELED,
) -> None:
    engine.close_order(execution_id, reason)


def test_balanced_two_leg_fills_complete_as_one_group() -> None:
    engine = PaperExecutionEngine()
    buy_id, sell_id = submit_group(engine)
    fill(engine, buy_id, "buy-fill", "0.01", 99990)
    fill(engine, sell_id, "sell-fill", "0.01", 100100)

    result = engine.reconcile_group("group-1")

    assert result.state is GroupReconciliationState.BALANCED
    assert result.matched_quantity == Decimal("0.01")
    assert result.residual is None
    assert result.post_hedge_residual_quantity == 0
    assert engine.orchestrator.current_state(buy_id) is ExecutionState.COMPLETED
    assert engine.orchestrator.current_state(sell_id) is ExecutionState.COMPLETED


def test_equal_partial_fills_are_balanced_at_reconciliation() -> None:
    engine = PaperExecutionEngine()
    buy_id, sell_id = submit_group(engine)
    fill(engine, buy_id, "buy-fill", "0.004")
    fill(engine, sell_id, "sell-fill", "0.004")
    close(engine, buy_id)
    close(engine, sell_id, OrderCloseReason.EXPIRED)

    result = engine.reconcile_group("group-1")

    assert result.state is GroupReconciliationState.BALANCED
    assert result.matched_quantity == Decimal("0.004")
    assert result.residual is None
    assert engine.orchestrator.current_state(buy_id) is ExecutionState.COMPLETED
    assert engine.orchestrator.current_state(sell_id) is ExecutionState.COMPLETED


def test_mismatched_partial_fills_detect_signed_residual() -> None:
    engine = PaperExecutionEngine()
    buy_id, sell_id = submit_group(engine)
    fill(engine, buy_id, "buy-fill", "0.01")
    fill(engine, sell_id, "sell-fill", "0.006")
    close(engine, sell_id)

    result = engine.reconcile_group("group-1")

    assert result.state is GroupReconciliationState.HEDGE_REQUIRED
    assert result.hedge_required is True
    assert result.residual is not None
    assert result.residual.signed_quantity == Decimal("0.004")
    assert result.residual.hedge_side is Side.SELL
    assert result.residual.hedge_quantity == Decimal("0.004")
    assert engine.orchestrator.current_state(buy_id) is ExecutionState.HEDGE_REQUIRED
    assert engine.orchestrator.current_state(sell_id) is ExecutionState.HEDGE_REQUIRED


def test_short_residual_requires_buy_hedge() -> None:
    engine = PaperExecutionEngine()
    buy_id, sell_id = submit_group(engine)
    fill(engine, buy_id, "buy-fill", "0.003")
    fill(engine, sell_id, "sell-fill", "0.01")
    close(engine, buy_id, OrderCloseReason.EXPIRED)

    result = engine.reconcile_group("group-1")

    assert result.residual is not None
    assert result.residual.signed_quantity == Decimal("-0.007")
    assert result.residual.hedge_side is Side.BUY
    assert result.residual.hedge_quantity == Decimal("0.007")


def test_paper_residual_hedge_flattens_and_audits_group() -> None:
    engine = PaperExecutionEngine()
    buy_id, sell_id = submit_group(engine)
    fill(engine, buy_id, "buy-fill", "0.01")
    fill(engine, sell_id, "sell-fill", "0.006")
    close(engine, sell_id)
    engine.reconcile_group("group-1")

    result = engine.hedge_residual(
        "group-1",
        venue=Venue.BINANCE,
        fill_id="hedge-fill",
        price=Decimal(100010),
        reference_price=Decimal(100000),
    )

    assert result.state is GroupReconciliationState.HEDGED
    assert result.hedge_execution_id is not None
    assert result.post_hedge_residual_quantity == 0
    hedge = engine.orchestrator.snapshot(result.hedge_execution_id)
    assert hedge.execution_role is ExecutionRole.RESIDUAL_HEDGE
    assert hedge.filled_quantity == Decimal("0.004")
    assert hedge.state is ExecutionState.COMPLETED
    assert engine.orchestrator.current_state(buy_id) is ExecutionState.COMPLETED
    assert engine.orchestrator.current_state(sell_id) is ExecutionState.COMPLETED


@pytest.mark.parametrize(
    ("engine", "price", "message"),
    [
        (
            PaperExecutionEngine(max_residual_hedge_notional=Decimal(100)),
            Decimal(100000),
            "notional limit",
        ),
        (
            PaperExecutionEngine(max_residual_hedge_slippage_bps=Decimal(5)),
            Decimal(99000),
            "slippage limit",
        ),
    ],
)
def test_unsafe_paper_hedge_halts_group(
    engine: PaperExecutionEngine,
    price: Decimal,
    message: str,
) -> None:
    buy_id, sell_id = submit_group(engine)
    fill(engine, buy_id, "buy-fill", "0.01")
    fill(engine, sell_id, "sell-fill", "0.006")
    close(engine, sell_id)
    engine.reconcile_group("group-1")

    result = engine.hedge_residual(
        "group-1",
        venue=Venue.BINANCE,
        fill_id="hedge-fill",
        price=price,
        reference_price=Decimal(100000),
    )

    assert result.state is GroupReconciliationState.HALTED
    assert message in result.message
    assert result.hedge_execution_id is None
    assert result.post_hedge_residual_quantity == Decimal("0.004")
    assert engine.orchestrator.current_state(buy_id) is ExecutionState.HALTED
    assert engine.orchestrator.current_state(sell_id) is ExecutionState.HALTED


def test_reconciliation_requires_exactly_two_valid_primary_legs() -> None:
    engine = PaperExecutionEngine()
    engine.submit(
        intent(Venue.BINANCE, Side.BUY),
        RiskDecision(True, "ok"),
        execution_group_id="group-1",
    )

    with pytest.raises(InvalidExecutionGroupError, match="exactly two"):
        engine.reconcile_group("group-1")
    with pytest.raises(InvalidExecutionGroupError, match="opposite sides"):
        engine.submit(
            intent(Venue.BYBIT, Side.BUY),
            RiskDecision(True, "ok"),
            execution_group_id="group-1",
        )


def test_reconciliation_rejects_open_orders_and_close_is_idempotent() -> None:
    engine = PaperExecutionEngine()
    buy_id, sell_id = submit_group(engine)
    fill(engine, buy_id, "buy-fill", "0.004")
    fill(engine, sell_id, "sell-fill", "0.004")

    with pytest.raises(InvalidExecutionTransition, match="before order closure"):
        engine.reconcile_group("group-1")

    first_close = engine.close_order(buy_id, OrderCloseReason.CANCELED)
    duplicate_close = engine.close_order(buy_id, OrderCloseReason.CANCELED)
    engine.close_order(sell_id, OrderCloseReason.EXPIRED)

    assert duplicate_close["event_id"] == first_close["event_id"]
    assert duplicate_close["state"] == ExecutionState.CANCELED.value
    with pytest.raises(InvalidExecutionTransition, match="execution is canceled"):
        engine.close_order(buy_id, OrderCloseReason.EXPIRED)
    assert engine.reconcile_group("group-1").state is GroupReconciliationState.BALANCED


def test_unfilled_closed_leg_is_included_in_residual_detection() -> None:
    engine = PaperExecutionEngine()
    buy_id, sell_id = submit_group(engine)
    fill(engine, buy_id, "buy-fill", "0.01")
    close(engine, sell_id)

    result = engine.reconcile_group("group-1")

    assert result.residual is not None
    assert result.residual.signed_quantity == Decimal("0.01")
    assert result.residual.hedge_side is Side.SELL


def test_live_execution_remains_unavailable() -> None:
    engine = PaperExecutionEngine()

    assert not hasattr(engine, "submit_live")
