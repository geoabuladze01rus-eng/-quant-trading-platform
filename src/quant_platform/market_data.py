from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from .domain import Quote, Venue


@dataclass(slots=True)
class MarketDataStore:
    """In-memory quote cache for the first paper-trading milestone."""

    quotes: dict[tuple[Venue, str], Quote]

    def __init__(self) -> None:
        self.quotes = {}

    def update(self, quote: Quote) -> None:
        self.quotes[(quote.venue, quote.symbol)] = quote

    def get(self, venue: Venue, symbol: str) -> Quote | None:
        return self.quotes.get((venue, symbol))

    def snapshot(self, symbol: str) -> list[Quote]:
        return [q for (venue, pair), q in self.quotes.items() if pair == symbol]

    def is_fresh(self, quote: Quote, max_age_ms: int = 1500) -> bool:
        age_ms = (datetime.now(UTC) - quote.timestamp).total_seconds() * 1000
        return age_ms <= max_age_ms


def quote_from_levels(
    venue: Venue,
    symbol: str,
    bid: str | Decimal,
    ask: str | Decimal,
    bid_size: str | Decimal,
    ask_size: str | Decimal,
) -> Quote:
    return Quote.now(
        venue,
        symbol,
        Decimal(str(bid)),
        Decimal(str(ask)),
        Decimal(str(bid_size)),
        Decimal(str(ask_size)),
    )
