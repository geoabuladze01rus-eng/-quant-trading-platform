"""Market-data quality and latency guard. Fails closed on unsafe quotes."""
from dataclasses import dataclass
from decimal import Decimal

from strategies.inter_exchange_arbitrage import Quote


@dataclass(frozen=True)
class QualityLimits:
    max_age_ms: int = 500
    max_cross_venue_skew_ms: int = 100
    max_spread_bps: Decimal = Decimal(100)
    min_size: Decimal = Decimal("0.001")

class QuoteQualityGuard:
    def __init__(self, limits: QualityLimits | None = None) -> None:
        self.limits = limits or QualityLimits()

    def valid(self, quote: Quote, now_ms: int) -> bool:
        if quote.timestamp_ms <= 0 or now_ms < quote.timestamp_ms:
            return False
        if now_ms - quote.timestamp_ms > self.limits.max_age_ms:
            return False
        if quote.bid <= 0 or quote.ask <= 0 or quote.bid > quote.ask:
            return False
        if quote.ask_size < self.limits.min_size or quote.bid_size < self.limits.min_size:
            return False
        spread_bps = (quote.ask - quote.bid) / quote.bid * Decimal(10000)
        return spread_bps <= self.limits.max_spread_bps

    def pair_valid(self, buy: Quote, sell: Quote, now_ms: int) -> bool:
        if not self.valid(buy, now_ms) or not self.valid(sell, now_ms):
            return False
        return abs(buy.timestamp_ms - sell.timestamp_ms) <= self.limits.max_cross_venue_skew_ms
