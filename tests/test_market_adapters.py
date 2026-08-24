from decimal import Decimal

from market.adapters.binance_market_data import BinanceMarketDataAdapter
from market.adapters.bybit_market_data import BybitMarketDataAdapter
from market.adapters.okx_market_data import OKXMarketDataAdapter


def test_adapters_normalize_ticker():
    out = []
    for cls in (BinanceMarketDataAdapter, BybitMarketDataAdapter, OKXMarketDataAdapter):
        a = cls(on_ticker=out.append)
        a.handle_ticker('BTCUSDT', '100', '101', 123)
    assert [x.venue for x in out] == ['BINANCE', 'BYBIT', 'OKX']
    assert all(x.bid == Decimal(100) and x.ask == Decimal(101) for x in out)

def test_binance_normalizes_orderbook_and_trade():
    books, trades = [], []
    a = BinanceMarketDataAdapter(on_order_book=books.append, on_trade=trades.append)
    a.handle_order_book('BTCUSDT', [('100','2')], [('101','3')], 1)
    a.handle_trade('BTCUSDT', 'BUY', '101', '0.5', 2)
    assert books[0].bids[0] == (Decimal(100), Decimal(2))
    assert trades[0].price == Decimal(101)
