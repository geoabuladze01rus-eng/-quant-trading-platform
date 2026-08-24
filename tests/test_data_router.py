from market.data_router import MarketDataRouter
from market.normalized_orderbook import OrderBookNormalizer


def book(ts=100, seq=1, bid='101', ask='102'):
    return OrderBookNormalizer.normalize('BINANCE','BTCUSDT',ts,[(bid,'1')],[(ask,'1')],seq)

def test_accepts_fresh_valid_book():
    r = MarketDataRouter(2000); r.register_venue('BINANCE'); r.connections['BINANCE'].connected(100)
    out = r.ingest(book(), 200)
    assert out.accepted and out.reason == 'accepted'

def test_rejects_stale_book():
    r = MarketDataRouter(1000); r.register_venue('BINANCE'); r.connections['BINANCE'].connected(100)
    out = r.ingest(book(ts=100), 1200)
    assert not out.accepted and out.reason == 'stale_book'

def test_rejects_out_of_order_sequence():
    r = MarketDataRouter(); r.register_venue('BINANCE'); r.connections['BINANCE'].connected(100)
    assert r.ingest(book(seq=5), 100).accepted
    out = r.ingest(book(seq=4), 101)
    assert not out.accepted and out.reason == 'out_of_order_sequence'
