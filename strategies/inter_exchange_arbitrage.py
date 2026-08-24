"""Cost-aware inter-exchange arbitrage signal generation."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Quote:
    venue: str
    symbol: str
    bid: Decimal
    ask: Decimal
    bid_size: Decimal = Decimal(0)
    ask_size: Decimal = Decimal(0)
    timestamp_ms: int = 0

@dataclass(frozen=True)
class ArbitrageSignal:
    buy_venue: str
    sell_venue: str
    symbol: str
    quantity: Decimal
    gross_edge: Decimal
    estimated_cost: Decimal
    net_edge: Decimal

class InterExchangeArbitrage:
    def __init__(self, fee_rates: dict[str, Decimal], slippage_bps: Decimal = Decimal(2), latency_buffer_bps: Decimal = Decimal(1), min_net_edge_bps: Decimal = Decimal(5), max_quote_age_ms: int = 1000) -> None:
        self.fee_rates = fee_rates
        self.slippage_bps = slippage_bps
        self.latency_buffer_bps = latency_buffer_bps
        self.min_net_edge_bps = min_net_edge_bps
        self.max_quote_age_ms = max_quote_age_ms

    def scan(self, quotes: list[Quote], now_ms: int) -> ArbitrageSignal | None:
        fresh = [q for q in quotes if 0 <= now_ms - q.timestamp_ms <= self.max_quote_age_ms and q.bid > 0 and q.ask > 0]
        best: ArbitrageSignal | None = None
        for buy in fresh:
            for sell in fresh:
                if buy.venue == sell.venue or buy.symbol != sell.symbol or buy.ask >= sell.bid:
                    continue
                qty = min(buy.ask_size, sell.bid_size)
                if qty <= 0:
                    continue
                gross = (sell.bid - buy.ask) / buy.ask
                costs = self.fee_rates.get(buy.venue, Decimal(0)) + self.fee_rates.get(sell.venue, Decimal(0)) + (self.slippage_bps + self.latency_buffer_bps) / Decimal(10000)
                net = gross - costs
                if net * Decimal(10000) < self.min_net_edge_bps:
                    continue
                signal = ArbitrageSignal(buy.venue, sell.venue, buy.symbol, qty, gross, costs, net)
                if best is None or signal.net_edge > best.net_edge:
                    best = signal
        return best
