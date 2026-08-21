from decimal import Decimal
from strategies.inter_exchange_arbitrage import InterExchangeArbitrage, Quote

def q(venue: str, bid: str, ask: str, ts: int = 1000) -> Quote:
    return Quote(venue, "BTCUSDT", Decimal(bid), Decimal(ask), Decimal("1"), Decimal("1"), ts)

def test_signal_uses_net_edge_after_costs() -> None:
    strategy = InterExchangeArbitrage({"binance": Decimal("0.001"), "bybit": Decimal("0.001")}, min_net_edge_bps=Decimal("5"))
    signal = strategy.scan([q("binance", "100", "100"), q("bybit", "101", "101")], 1000)
    assert signal is not None
    assert signal.buy_venue == "binance"
    assert signal.sell_venue == "bybit"
    assert signal.net_edge > Decimal("0")

def test_stale_quote_is_rejected() -> None:
    strategy = InterExchangeArbitrage({}, max_quote_age_ms=100)
    assert strategy.scan([q("binance", "100", "100", 0), q("bybit", "101", "101", 1000)], 1000) is None
