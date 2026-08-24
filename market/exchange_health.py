"""Exchange health and latency scoring for fail-safe routing."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ExchangeHealth:
    venue: str
    latency_ms: int
    freshness_ms: int
    data_quality: Decimal
    available: bool
    score: Decimal

class ExchangeHealthMonitor:
    def __init__(self, max_latency_ms: int = 500, max_freshness_ms: int = 5000):
        self.max_latency_ms = max_latency_ms
        self.max_freshness_ms = max_freshness_ms

    def evaluate(self, venue: str, latency_ms: int, freshness_ms: int, data_quality: Decimal) -> ExchangeHealth:
        latency_ms = max(0, latency_ms)
        freshness_ms = max(0, freshness_ms)
        quality = max(Decimal(0), min(Decimal(1), data_quality))
        latency_score = max(Decimal(0), Decimal(1) - Decimal(latency_ms) / Decimal(self.max_latency_ms))
        freshness_score = max(Decimal(0), Decimal(1) - Decimal(freshness_ms) / Decimal(self.max_freshness_ms))
        score = min(latency_score, freshness_score, quality)
        available = latency_ms <= self.max_latency_ms and freshness_ms <= self.max_freshness_ms and quality > 0
        return ExchangeHealth(venue, latency_ms, freshness_ms, quality, available, score)
