"""Normalized exchange/broker data contract. Concrete adapters plug into this interface."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Protocol, Iterable

class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

@dataclass(frozen=True)
class Ticker:
    venue: str
    symbol: str
    bid: Decimal
    ask: Decimal
    timestamp_ms: int

@dataclass(frozen=True)
class OrderBook:
    venue: str
    symbol: str
    bids: tuple[tuple[Decimal, Decimal], ...]
    asks: tuple[tuple[Decimal, Decimal], ...]
    timestamp_ms: int

@dataclass(frozen=True)
class Trade:
    venue: str
    symbol: str
    side: Side
    price: Decimal
    quantity: Decimal
    timestamp_ms: int

@dataclass(frozen=True)
class Funding:
    venue: str
    symbol: str
    rate: Decimal
    timestamp_ms: int

class MarketDataAdapter(Protocol):
    venue: str
    def subscribe(self, symbols: Iterable[str]) -> None: ...
    def close(self) -> None: ...

class ExecutionAdapter(Protocol):
    venue: str
    def place_order(self, symbol: str, side: Side, quantity: Decimal, limit_price: Decimal | None = None) -> str: ...
    def cancel_order(self, order_id: str) -> None: ...
