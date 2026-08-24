from decimal import Decimal

from quant_platform.domain import Venue
from quant_platform.market_ws import (
    BinanceBookTickerCollector,
    BybitTickerCollector,
    OKXTickerCollector,
)


async def sink(_quote):
    return None


def test_binance_book_ticker_parser() -> None:
    collector = BinanceBookTickerCollector(Venue.BINANCE, "BTCUSDT", sink)
    quote = collector.parse_message({"b": "100", "a": "101", "B": "2", "A": "3"})
    assert quote is not None
    assert quote.bid == Decimal(100)
    assert quote.ask == Decimal(101)


def test_bybit_ticker_parser() -> None:
    collector = BybitTickerCollector(Venue.BYBIT, "BTCUSDT", sink)
    quote = collector.parse_message({
        "topic": "tickers.BTCUSDT",
        "data": {"bid1Price": "100", "ask1Price": "101", "bid1Size": "2", "ask1Size": "3"},
    })
    assert quote is not None
    assert quote.ask_size == Decimal(3)


def test_okx_ticker_parser() -> None:
    collector = OKXTickerCollector(Venue.OKX, "BTC-USDT", sink)
    quote = collector.parse_message({
        "arg": {"channel": "tickers", "instId": "BTC-USDT"},
        "data": [{"bidPx": "100", "askPx": "101", "bidSz": "2", "askSz": "3"}],
    })
    assert quote is not None
    assert quote.mid == Decimal("100.5")
