"""Normalized market-data adapter interfaces for live/paper venues."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, Iterable
from strategies.inter_exchange_arbitrage import Quote

@dataclass(frozen=True)
class RawBookTicker:
    symbol: str
    bid: Decimal
    ask: Decimal
    bid_size: Decimal
    ask_size: Decimal
    timestamp_ms: int

class ExchangeMarketDataAdapter(Protocol):
    venue: str
    def normalize(self, raw: RawBookTicker) -> Quote: ...

class BinanceAdapter:
    venue = "binance"
    def normalize(self, raw: RawBookTicker) -> Quote:
        return Quote(self.venue, raw.symbol, raw.bid, raw.ask, raw.bid_size, raw.ask_size, raw.timestamp_ms)

class BybitAdapter:
    venue = "bybit"
    def normalize(self, raw: RawBookTicker) -> Quote:
        return Quote(self.venue, raw.symbol, raw.bid, raw.ask, raw.bid_size, raw.ask_size, raw.timestamp_ms)

class OKXAdapter:
    venue = "okx"
    def normalize(self, raw: RawBookTicker) -> Quote:
        return Quote(self.venue, raw.symbol, raw.bid, raw.ask, raw.bid_size, raw.ask_size, raw.timestamp_ms)

class QuoteAggregator:
    def __init__(self, adapters: Iterable[ExchangeMarketDataAdapter]) -> None:
        self.adapters = {adapter.venue: adapter for adapter in adapters}

    def normalize(self, venue: str, raw: RawBookTicker) -> Quote:
        return self.adapters[venue].normalize(raw)
