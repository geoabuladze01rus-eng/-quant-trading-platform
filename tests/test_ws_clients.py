from decimal import Decimal
from marketdata.ws_clients import BookTickerParser

def test_binance_parser():
    q = BookTickerParser.binance({"s":"BTCUSDT","b":"100","a":"101","B":"2","A":"3","E":1234})
    assert q.symbol == "BTCUSDT" and q.bid == Decimal("100") and q.ask_size == Decimal("3")

def test_bybit_parser():
    q = BookTickerParser.bybit({"ts":1234,"data":{"s":"BTCUSDT","b":"100","a":"101","B":"2","A":"3"}})
    assert q.bid_size == Decimal("2") and q.timestamp_ms == 1234

def test_okx_parser():
    q = BookTickerParser.okx({"ts":"1234","data":[{"instId":"BTC-USDT","bidPx":"100","askPx":"101","bidSz":"2","askSz":"3"}]})
    assert q.symbol == "BTC-USDT" and q.ask == Decimal("101")
