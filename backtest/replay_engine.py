"""Deterministic market-event replay engine for backtests and paper validation."""
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class MarketEvent:
    timestamp_ms: int
    venue: str
    symbol: str
    bid: Decimal
    ask: Decimal
    bid_qty: Decimal
    ask_qty: Decimal

class ReplayEngine:
    def __init__(self, events: Iterable[MarketEvent]):
        self.events = sorted(events, key=lambda e: e.timestamp_ms)
        self.current_timestamp_ms = None
        self.processed = 0

    def run(self, on_event: Callable[[MarketEvent], None]) -> int:
        for event in self.events:
            self.current_timestamp_ms = event.timestamp_ms
            on_event(event)
            self.processed += 1
        return self.processed

    def reset(self) -> None:
        self.current_timestamp_ms = None
        self.processed = 0
