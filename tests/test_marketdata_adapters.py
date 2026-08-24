from decimal import Decimal

from marketdata.adapters import (
    BinanceAdapter,
    BybitAdapter,
    OKXAdapter,
    QuoteAggregator,
    RawBookTicker,
)


def test_all_adapters_normalize_to_same_quote_contract():
    raw = RawBookTicker("BTCUSDT", Decimal(100), Decimal(101), Decimal(2), Decimal(3), 1000)
    agg = QuoteAggregator([BinanceAdapter(), BybitAdapter(), OKXAdapter()])
    for venue in ("binance", "bybit", "okx"):
        quote = agg.normalize(venue, raw)
        assert quote.venue == venue
        assert quote.symbol == "BTCUSDT"
        assert quote.bid == Decimal(100)
        assert quote.ask_size == Decimal(3)
