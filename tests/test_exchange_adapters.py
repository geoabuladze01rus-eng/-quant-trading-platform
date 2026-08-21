from decimal import Decimal
from market.exchange_adapters import BinanceAdapter, BybitAdapter, OkxAdapter

def test_binance_adapter():
    b = BinanceAdapter().parse_book({'s':'BTCUSDT','E':100,'u':7,'b':[['101','2']], 'a':[['102','3']]})
    assert b.venue == 'BINANCE' and b.best_bid.price == Decimal('101') and b.best_ask.price == Decimal('102')

def test_bybit_adapter():
    b = BybitAdapter().parse_book({'ts':200,'data':{'s':'BTCUSDT','u':8,'b':[['101','2']], 'a':[['102','3']]}})
    assert b.venue == 'BYBIT' and b.sequence == 8

def test_okx_adapter():
    b = OkxAdapter().parse_book({'data':[{'instId':'BTC-USDT','ts':'300','seqId':9,'bids':[['101','2']], 'asks':[['102','3']]}]})
    assert b.venue == 'OKX' and b.symbol == 'BTC-USDT' and b.sequence == 9
