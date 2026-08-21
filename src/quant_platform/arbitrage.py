from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .domain import Quote, Venue


@dataclass(frozen=True, slots=True)
class ArbitrageOpportunity:
    symbol: str
    buy_venue: Venue
    sell_venue: Venue
    buy_price: Decimal
    sell_price: Decimal
    quantity: Decimal
    gross_edge_bps: Decimal
    fees_bps: Decimal
    slippage_bps: Decimal
    latency_buffer_bps: Decimal
    net_edge_bps: Decimal

    @property
    def profitable(self) -> bool:
        return self.net_edge_bps > 0


@dataclass(frozen=True, slots=True)
class ArbitrageScanner:
    min_net_edge_bps: Decimal = Decimal("8")
    taker_fee_bps: Decimal = Decimal("5")
    expected_slippage_bps: Decimal = Decimal("2")
    latency_buffer_bps: Decimal = Decimal("1")
    max_quote_age_ms: int = 1500

    def scan(self, quotes: list[Quote], quantity: Decimal) -> ArbitrageOpportunity | None:
        best: ArbitrageOpportunity | None = None
        for buy in quotes:
            for sell in quotes:
                if buy.venue == sell.venue or buy.symbol != sell.symbol:
                    continue
                if buy.ask <= 0 or sell.bid <= 0:
                    continue
                gross_edge_bps = (sell.bid - buy.ask) / buy.ask * Decimal("10000")
                fees_bps = self.taker_fee_bps * Decimal("2")
                net_edge_bps = gross_edge_bps - fees_bps - self.expected_slippage_bps - self.latency_buffer_bps
                candidate = ArbitrageOpportunity(
                    symbol=buy.symbol,
                    buy_venue=buy.venue,
                    sell_venue=sell.venue,
                    buy_price=buy.ask,
                    sell_price=sell.bid,
                    quantity=quantity,
                    gross_edge_bps=gross_edge_bps,
                    fees_bps=fees_bps,
                    slippage_bps=self.expected_slippage_bps,
                    latency_buffer_bps=self.latency_buffer_bps,
                    net_edge_bps=net_edge_bps,
                )
                if candidate.net_edge_bps >= self.min_net_edge_bps and (best is None or candidate.net_edge_bps > best.net_edge_bps):
                    best = candidate
        return best
