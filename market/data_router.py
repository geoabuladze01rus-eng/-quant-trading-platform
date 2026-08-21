"""Validated multi-venue market data router."""
from dataclasses import dataclass
from market.normalized_orderbook import NormalizedOrderBook
from market.connection_manager import ConnectionManager

@dataclass(frozen=True)
class RoutedBook:
    book: NormalizedOrderBook
    accepted: bool
    reason: str

class MarketDataRouter:
    def __init__(self, max_age_ms: int = 2000):
        if max_age_ms <= 0: raise ValueError("max_age_ms must be positive")
        self.max_age_ms = max_age_ms
        self.connections = {}
        self.latest = {}

    def register_venue(self, venue, connection=None):
        self.connections[venue] = connection or ConnectionManager(self.max_age_ms)

    def ingest(self, book, now_ms):
        connection = self.connections.get(book.venue)
        if connection is None: return RoutedBook(book, False, "unregistered_venue")
        if connection.check_stale(now_ms): return RoutedBook(book, False, "stale_connection")
        if book.timestamp_ms > now_ms or now_ms - book.timestamp_ms > self.max_age_ms:
            return RoutedBook(book, False, "stale_book")
        if book.best_bid is None or book.best_ask is None or book.best_bid.price >= book.best_ask.price:
            return RoutedBook(book, False, "invalid_crossed_book")
        previous = self.latest.get((book.venue, book.symbol))
        if previous and previous.sequence is not None and book.sequence is not None and book.sequence <= previous.sequence:
            return RoutedBook(book, False, "out_of_order_sequence")
        self.latest[(book.venue, book.symbol)] = book
        return RoutedBook(book, True, "accepted")
