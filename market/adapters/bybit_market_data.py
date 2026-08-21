"""Bybit market-data adapter skeleton with normalized callbacks."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Callable
from market.exchange_adapter import Ticker, OrderBook, Trade, Side

@dataclass
class BybitMarketDataAdapter:
    venue: str = "BYBIT"
    on_ticker: Callable[[Ticker], None] | None = None
    on_order_book: Callable[[OrderBook], None] | None = None
    on_trade: Callable[[Trade], None] | None = None

    def handle_ticker(self, symbol: str, bid: str, ask: str, timestamp_ms: int) -> None:
        event = Ticker(self.venue, symbol, Decimal(bid), Decimal(ask), timestamp_ms)
        if self.on_ticker: self.on_ticker(event)

    def handle_trade(self, symbol: str, side: str, price: str, quantity: str, timestamp_ms: int) -> None:
        event = Trade(self.venue, symbol, Side(side.upper()), Decimal(price), Decimal(quantity), timestamp_ms)
        if self.on_trade: self.on_trade(event)

    def handle_order_book(self, symbol: str, bids: list[tuple[str, str]], asks: list[tuple[str, str]], timestamp_ms: int) -> None:
        event = OrderBook(self.venue, symbol, tuple((Decimal(p), Decimal(q)) for p, q in bids), tuple((Decimal(p), Decimal(q)) for p, q in asks), timestamp_ms)
        if self.on_order_book: self.on_order_book(event)
