"""Market-data quality scoring and fail-safe checks."""
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class DataQuality:
    score: Decimal
    stale: bool
    sequence_gap: bool
    crossed_book: bool
    timestamp_anomaly: bool
    spread_bps: Decimal

class DataQualityMonitor:
    def __init__(self, stale_after_ms: int = 5000, max_spread_bps: Decimal = Decimal("500")):
        self.stale_after_ms = stale_after_ms
        self.max_spread_bps = max_spread_bps

    def evaluate(self, bid: Decimal, ask: Decimal, event_timestamp_ms: int, now_ms: int, sequence_gap: bool = False) -> DataQuality:
        timestamp_anomaly = event_timestamp_ms > now_ms + 1000 or event_timestamp_ms < 0
        stale = now_ms - event_timestamp_ms > self.stale_after_ms
        crossed = bid <= 0 or ask <= 0 or ask < bid
        if bid > 0 and ask >= bid:
            spread_bps = (ask - bid) / ((ask + bid) / Decimal("2")) * Decimal("10000")
        else:
            spread_bps = Decimal("999999")
        score = Decimal("1")
        if stale: score -= Decimal("0.35")
        if sequence_gap: score -= Decimal("0.35")
        if crossed: score -= Decimal("0.50")
        if timestamp_anomaly: score -= Decimal("0.35")
        if not crossed and spread_bps > self.max_spread_bps: score -= Decimal("0.20")
        score = max(Decimal("0"), min(Decimal("1"), score))
        return DataQuality(score, stale, sequence_gap, crossed, timestamp_anomaly, spread_bps)
