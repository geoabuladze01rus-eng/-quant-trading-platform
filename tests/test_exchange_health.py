from decimal import Decimal

from market.exchange_health import ExchangeHealthMonitor


def test_healthy_exchange_is_available():
    h = ExchangeHealthMonitor().evaluate('BINANCE', 50, 100, Decimal('0.99'))
    assert h.available
    assert h.score == Decimal('0.90')

def test_stale_exchange_is_disabled():
    h = ExchangeHealthMonitor().evaluate('OKX', 50, 6000, Decimal(1))
    assert not h.available
    assert h.score == Decimal(0)

def test_high_latency_is_disabled():
    h = ExchangeHealthMonitor().evaluate('BYBIT', 501, 100, Decimal(1))
    assert not h.available
    assert h.score == Decimal(0)
