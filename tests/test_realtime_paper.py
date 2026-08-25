import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest

from quant_platform.domain import OrderIntent, Quote, Side, Venue
from quant_platform.execution import PaperExecutionEngine
from quant_platform.execution_orchestrator import (
    GroupReconciliationState,
    InvalidCheckpointError,
)
from quant_platform.pipeline import PaperArbitragePipeline
from quant_platform.realtime_paper import (
    QuoteCache,
    RealtimePaperArbitrage,
    build_default_runtime,
)
from quant_platform.risk import RiskDecision


def quote(venue: Venue, bid: str, ask: str, seconds_ago: float = 0) -> Quote:
    return Quote(
        venue=venue,
        symbol="BTCUSDT",
        bid=Decimal(bid),
        ask=Decimal(ask),
        bid_size=Decimal(1),
        ask_size=Decimal(1),
        timestamp=datetime.now(UTC) - timedelta(seconds=seconds_ago),
    )


def order_intent(venue: Venue, side: Side) -> OrderIntent:
    return OrderIntent(
        venue=venue,
        symbol="BTCUSDT",
        side=side,
        quantity=Decimal("0.01"),
        limit_price=Decimal(100000),
        strategy="arbitrage",
        reason="realtime recovery test",
    )


def submit_group(engine: PaperExecutionEngine) -> tuple[str, str]:
    risk = RiskDecision(True, "ok")
    buy = engine.submit(
        order_intent(Venue.BINANCE, Side.BUY),
        risk,
        execution_group_id="runtime-group",
    )
    sell = engine.submit(
        order_intent(Venue.BYBIT, Side.SELL),
        risk,
        execution_group_id="runtime-group",
    )
    return buy["execution_id"], sell["execution_id"]


def test_quote_cache_returns_only_fresh_quotes() -> None:
    cache = QuoteCache()
    cache.update(quote(Venue.BINANCE, "100", "101"))
    cache.update(quote(Venue.BYBIT, "100", "101", seconds_ago=5))

    snapshot = cache.snapshot("BTCUSDT", (Venue.BINANCE, Venue.BYBIT), max_age_ms=1500)

    assert [item.venue for item in snapshot] == [Venue.BINANCE]


def test_runtime_waits_for_two_venues_before_pipeline() -> None:
    runtime = RealtimePaperArbitrage()
    calls: list[tuple[list[Quote], Decimal, Decimal]] = []

    def fake_run(
        _pipeline: PaperArbitragePipeline,
        quotes: list[Quote],
        portfolio: Decimal,
        quantity: Decimal,
    ) -> None:
        calls.append((quotes, portfolio, quantity))

    with patch.object(PaperArbitragePipeline, "run", fake_run):
        async def scenario() -> None:
            await runtime.on_quote(quote(Venue.BINANCE, "100", "101"))
            assert calls == []
            await runtime.on_quote(quote(Venue.BYBIT, "102", "103"))

        asyncio.run(scenario())

    assert len(calls) == 1
    assert {item.venue for item in calls[0][0]} == {Venue.BINANCE, Venue.BYBIT}
    assert calls[0][1] == Decimal(100000)
    assert calls[0][2] == Decimal("0.001")


def test_default_runtime_restores_and_continues_checkpoint(tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "runtime" / "execution.json"
    runtime = build_default_runtime(checkpoint_path=checkpoint_path)
    buy_id, sell_id = submit_group(runtime.execution)
    runtime.execution.process_fill(
        buy_id,
        fill_id="fill-before-restart",
        quantity=Decimal("0.004"),
        price=Decimal(99990),
    )

    recovered = build_default_runtime(checkpoint_path=checkpoint_path)

    assert recovered.execution.orchestrator.snapshot(buy_id).filled_quantity == Decimal(
        "0.004"
    )
    assert recovered.execution.orchestrator.snapshot(sell_id).filled_quantity == 0
    recovered.execution.process_fill(
        sell_id,
        fill_id="fill-after-restart",
        quantity=Decimal("0.004"),
        price=Decimal(100100),
    )
    second_recovery = build_default_runtime(checkpoint_path=checkpoint_path)
    assert second_recovery.execution.orchestrator.snapshot(sell_id).filled_quantity == Decimal(
        "0.004"
    )


def test_default_runtime_refuses_corrupted_checkpoint(tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "runtime" / "execution.json"
    checkpoint_path.parent.mkdir(parents=True)
    checkpoint_path.write_text("corrupted", encoding="utf-8")

    with pytest.raises(InvalidCheckpointError, match="cannot read"):
        build_default_runtime(checkpoint_path=checkpoint_path)


def test_runtime_watchdog_audits_residual_without_guessing_hedge_price() -> None:
    runtime = RealtimePaperArbitrage(execution_timeout_seconds=5)
    buy_id, sell_id = submit_group(runtime.execution)
    runtime.execution.process_fill(
        buy_id,
        fill_id="buy-fill",
        quantity=Decimal("0.01"),
        price=Decimal(99990),
    )
    runtime.execution.process_fill(
        sell_id,
        fill_id="sell-fill",
        quantity=Decimal("0.004"),
        price=Decimal(100100),
    )
    submitted_at = runtime.execution.orchestrator.group_snapshots()[0].submitted_at

    (result,) = runtime.sweep_execution_timeouts(
        now=submitted_at + timedelta(seconds=6)
    )

    assert result.reconciliation is not None
    assert result.reconciliation.state is GroupReconciliationState.HEDGE_REQUIRED
    event = runtime.audit.last()
    assert event is not None
    assert event["event_type"] == "execution_group_timeout"
    assert event["hedge_required"] is True
    assert event["residual_signed_quantity"] == "0.006"
    assert result.reconciliation.hedge_execution_id is None


@pytest.mark.parametrize(
    ("timeout", "interval"),
    [(0.0, 1.0), (5.0, float("nan"))],
)
def test_runtime_rejects_invalid_watchdog_configuration(
    timeout: float,
    interval: float,
) -> None:
    with pytest.raises(ValueError, match="finite and positive"):
        RealtimePaperArbitrage(
            execution_timeout_seconds=timeout,
            timeout_sweep_interval_seconds=interval,
        )
