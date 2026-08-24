import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

from quant_platform.domain import Quote, Venue
from quant_platform.pipeline import PaperArbitragePipeline
from quant_platform.realtime_paper import QuoteCache, RealtimePaperArbitrage


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
