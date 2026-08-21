from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum


class Side(StrEnum):
    BUY = "buy"
    SELL = "sell"


class Venue(StrEnum):
    BINANCE = "binance"
    BYBIT = "bybit"
    OKX = "okx"
    TINVEST = "tinvest"


@dataclass(frozen=True, slots=True)
class Quote:
    venue: Venue
    symbol: str
    bid: Decimal
    ask: Decimal
    bid_size: Decimal
    ask_size: Decimal
    timestamp: datetime

    @classmethod
    def now(cls, venue: Venue, symbol: str, bid: Decimal, ask: Decimal,
            bid_size: Decimal, ask_size: Decimal) -> "Quote":
        return cls(venue, symbol, bid, ask, bid_size, ask_size, datetime.now(timezone.utc))

    @property
    def mid(self) -> Decimal:
        return (self.bid + self.ask) / Decimal("2")

    @property
    def spread_bps(self) -> Decimal:
        if self.mid == 0:
            return Decimal("0")
        return (self.ask - self.bid) / self.mid * Decimal("10000")


@dataclass(frozen=True, slots=True)
class OrderIntent:
    venue: Venue
    symbol: str
    side: Side
    quantity: Decimal
    limit_price: Decimal | None
    strategy: str
    reason: str
