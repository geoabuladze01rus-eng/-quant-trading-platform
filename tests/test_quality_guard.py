from decimal import Decimal

from marketdata.quality_guard import QualityLimits, QuoteQualityGuard
from strategies.inter_exchange_arbitrage import Quote


def quote(bid="100", ask="101", ts=1000, size="1"):
    return Quote("binance", "BTCUSDT", Decimal(bid), Decimal(ask), Decimal(size), Decimal(size), ts)

def test_rejects_stale_quote():
    assert not QuoteQualityGuard().valid(quote(ts=400), 1000)

def test_rejects_inverted_market():
    assert not QuoteQualityGuard().valid(quote("101", "100"), 1000)

def test_rejects_wide_spread():
    guard = QuoteQualityGuard(QualityLimits(max_spread_bps=Decimal(50)))
    assert not guard.valid(quote("100", "101"), 1000)

def test_pair_requires_low_timestamp_skew():
    guard = QuoteQualityGuard(QualityLimits(max_cross_venue_skew_ms=20))
    a = quote(ts=1000)
    b = Quote("bybit", "BTCUSDT", Decimal(100), Decimal(101), Decimal(1), Decimal(1), 1021)
    assert not guard.pair_valid(a, b, 1021)
