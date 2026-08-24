from decimal import Decimal

from backtesting.market_replay import MarketReplay, ReplayEvent
from strategies.inter_exchange_arbitrage import Quote


def q(venue: str, ts: int) -> Quote:
    return Quote(venue, "BTCUSDT", Decimal(100), Decimal(101), Decimal(1), Decimal(1), ts)

def test_replay_counts_stale_quotes_and_skew() -> None:
    events = [ReplayEvent(1000, (q("binance", 1000), q("bybit", 990))), ReplayEvent(3000, (q("binance", 1000), q("bybit", 2990)))]
    stats = MarketReplay(max_quote_age_ms=100).run(events, lambda event: True)
    assert stats.events == 2
    assert stats.opportunities == 2
    assert stats.stale_quotes == 2
    assert stats.average_cross_venue_skew_ms == Decimal(10)
