"""Deterministic market-data replay with timing/quality statistics."""
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from decimal import Decimal

from strategies.inter_exchange_arbitrage import Quote


@dataclass(frozen=True)
class ReplayEvent:
    timestamp_ms: int
    quotes: tuple[Quote, ...]

@dataclass(frozen=True)
class ReplayStats:
    events: int
    opportunities: int
    stale_quotes: int
    average_cross_venue_skew_ms: Decimal

class MarketReplay:
    def __init__(self, max_quote_age_ms: int = 1000) -> None:
        self.max_quote_age_ms = max_quote_age_ms

    def run(self, events: Iterable[ReplayEvent], on_event: Callable[[ReplayEvent], bool | None]) -> ReplayStats:
        count = opportunities = stale = 0
        skew_values: list[int] = []
        for event in events:
            count += 1
            stale_event = any(
                event.timestamp_ms - q.timestamp_ms > self.max_quote_age_ms
                for q in event.quotes
            )
            if stale_event:
                stale += len(event.quotes)
            else:
                timestamps = [q.timestamp_ms for q in event.quotes if q.timestamp_ms > 0]
                if len(timestamps) >= 2:
                    skew_values.append(max(timestamps) - min(timestamps))
            if on_event(event):
                opportunities += 1
        avg = Decimal(str(sum(skew_values) / len(skew_values))) if skew_values else Decimal(0)
        return ReplayStats(count, opportunities, stale, avg)
