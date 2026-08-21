"""Spot cross-venue arbitrage opportunity detection with conservative cost accounting."""
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class VenueQuote:
    venue: str
    bid: Decimal
    ask: Decimal
    bid_qty: Decimal
    ask_qty: Decimal
    health_score: Decimal = Decimal("1")
    available: bool = True

@dataclass(frozen=True)
class ArbitrageOpportunity:
    buy_venue: str
    sell_venue: str
    quantity: Decimal
    gross_edge_bps: Decimal
    estimated_cost_bps: Decimal
    net_edge_bps: Decimal
    executable: bool

class SpotArbitrageEngine:
    def __init__(self, min_net_edge_bps: Decimal = Decimal("10"), fee_bps: Decimal = Decimal("10"), slippage_bps: Decimal = Decimal("5"), latency_bps: Decimal = Decimal("2")):
        self.min_net_edge_bps = min_net_edge_bps
        self.fee_bps = fee_bps
        self.slippage_bps = slippage_bps
        self.latency_bps = latency_bps

    def find(self, quotes: list[VenueQuote]) -> list[ArbitrageOpportunity]:
        out = []
        for buy in quotes:
            for sell in quotes:
                if buy.venue == sell.venue or not buy.available or not sell.available:
                    continue
                if buy.ask <= 0 or sell.bid <= buy.ask or min(buy.health_score, sell.health_score) <= 0:
                    continue
                quantity = min(buy.ask_qty, sell.bid_qty)
                gross = (sell.bid - buy.ask) / buy.ask * Decimal("10000")
                health_penalty = (Decimal("1") - min(buy.health_score, sell.health_score)) * Decimal("20")
                costs = self.fee_bps * 2 + self.slippage_bps * 2 + self.latency_bps + health_penalty
                net = gross - costs
                out.append(ArbitrageOpportunity(buy.venue, sell.venue, quantity, gross, costs, net, net >= self.min_net_edge_bps))
        return sorted(out, key=lambda x: x.net_edge_bps, reverse=True)
