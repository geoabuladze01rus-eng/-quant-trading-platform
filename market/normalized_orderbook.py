"""Venue-neutral order book normalization."""
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class BookLevel:
    price: Decimal
    quantity: Decimal

@dataclass(frozen=True)
class NormalizedOrderBook:
    venue: str
    symbol: str
    timestamp_ms: int
    sequence: int | None
    bids: tuple[BookLevel, ...]
    asks: tuple[BookLevel, ...]

    @property
    def best_bid(self):
        return self.bids[0] if self.bids else None

    @property
    def best_ask(self):
        return self.asks[0] if self.asks else None

class OrderBookNormalizer:
    @staticmethod
    def normalize(venue, symbol, timestamp_ms, bids, asks, sequence=None):
        def levels(raw, reverse):
            result = [BookLevel(Decimal(str(p)), Decimal(str(q))) for p, q in raw if Decimal(str(p)) > 0 and Decimal(str(q)) > 0]
            return tuple(sorted(result, key=lambda x: x.price, reverse=reverse))
        return NormalizedOrderBook(venue, symbol, timestamp_ms, sequence, levels(bids, True), levels(asks, False))
