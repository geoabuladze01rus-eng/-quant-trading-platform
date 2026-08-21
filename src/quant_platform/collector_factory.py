from __future__ import annotations

from .domain import Venue
from .market_ws import (
    BinanceBookTickerCollector,
    BybitTickerCollector,
    OKXTickerCollector,
    QuoteHandler,
    WebSocketCollector,
)


def build_public_collector(venue: Venue, symbol: str, handler: QuoteHandler) -> WebSocketCollector:
    if venue is Venue.BINANCE:
        return BinanceBookTickerCollector(venue, symbol, handler)
    if venue is Venue.BYBIT:
        return BybitTickerCollector(venue, symbol, handler)
    if venue is Venue.OKX:
        return OKXTickerCollector(venue, symbol, handler)
    raise ValueError(f"websocket market-data collector is not implemented for {venue}")
