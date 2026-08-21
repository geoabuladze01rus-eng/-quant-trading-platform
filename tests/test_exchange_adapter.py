from decimal import Decimal
from market.exchange_adapter import Funding, OrderBook, Side, Ticker, Trade

def test_normalized_market_contracts():
    ticker = Ticker('BINANCE', 'BTCUSDT', Decimal('100'), Decimal('101'), 1)
    book = OrderBook('BYBIT', 'BTCUSDT', ((Decimal('100'), Decimal('2')),), ((Decimal('101'), Decimal('3')),), 2)
    trade = Trade('OKX', 'BTCUSDT', Side.BUY, Decimal('101'), Decimal('1'), 3)
    funding = Funding('BYBIT', 'BTCUSDT', Decimal('0.0001'), 4)
    assert ticker.ask > ticker.bid
    assert book.asks[0][1] == Decimal('3')
    assert trade.side == Side.BUY
    assert funding.rate > 0
