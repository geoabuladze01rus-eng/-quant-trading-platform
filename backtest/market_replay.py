"""Deterministic event-time market replay for backtests and paper trading."""
from collections.abc import Callable, Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class MarketEvent:
    timestamp_ms: int
    venue: str
    symbol: str
    payload: object

class MarketReplay:
    def __init__(self, events: Iterable[MarketEvent]):
        self.events = sorted(events, key=lambda e: e.timestamp_ms)

    def run(self, on_event: Callable[[MarketEvent], None], start_ms=None, end_ms=None):
        for event in self.events:
            if start_ms is not None and event.timestamp_ms < start_ms: continue
            if end_ms is not None and event.timestamp_ms > end_ms: continue
            on_event(event)

    def between(self, start_ms, end_ms):
        return [e for e in self.events if start_ms <= e.timestamp_ms <= end_ms]
