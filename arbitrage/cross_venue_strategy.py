"""Cross-venue spot arbitrage strategy orchestration.

The strategy is deliberately execution-agnostic: it produces a fully risk-gated
TradeIntent, while the execution layer remains responsible for submitting orders.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from arbitrage.opportunity_scanner import OpportunityScanner, Opportunity

@dataclass(frozen=True)
class StrategyConfig:
    min_edge_bps: Decimal
    max_data_age_ms: int
    max_spread_bps: Decimal
    min_confirmations: int
    max_book_imbalance: Decimal
    trade_pct: Decimal
    asset_pct: Decimal
    target_volatility: Decimal = Decimal("0")
    volatility_cap: Decimal = Decimal("1")

@dataclass(frozen=True)
class TradeIntent:
    opportunity: Opportunity
    quantity: Decimal
    notional: Decimal
    quality_score: Decimal
    net_edge_bps: Decimal
    approved: bool
    reason: str

class CrossVenueArbitrageStrategy:
    def __init__(self, scanner, quality_filter, persistence, position_sizer, risk_gate):
        self.scanner = scanner
        self.quality_filter = quality_filter
        self.persistence = persistence
        self.position_sizer = position_sizer
        self.risk_gate = risk_gate

    def evaluate(self, books: Iterable, fees: dict, equity, config: StrategyConfig,
                 market_age_ms: int, spread_bps: Decimal,
                 book_imbalance: Decimal, volatility: Decimal,
                 observations: dict[str, int], exposures: list, exposure_factory):
        opportunities = self.scanner.scan(books, Decimal("1"), fees, config.min_edge_bps)
        intents = []
        for opp in opportunities:
            stats = self.persistence.observe(
                market_age_ms, opp.net_edge_bps, config.min_edge_bps
            )
            confirmations = observations.get(opp.symbol, stats.confirmations)
            quality = self.quality_filter.evaluate(
                market_age_ms, config.max_data_age_ms,
                spread_bps, config.max_spread_bps,
                opp.net_edge_bps, config.min_edge_bps,
                confirmations, config.min_confirmations,
                book_imbalance, config.max_book_imbalance,
            )
            if not quality.approved:
                intents.append(TradeIntent(opp, Decimal(0), Decimal(0), quality.score,
                                            opp.net_edge_bps, False, quality.reason))
                continue

            size = self.position_sizer.size(
                opp.quantity, opp.buy_price, opp.quantity, equity,
                config.trade_pct, config.asset_pct, opp.net_edge_bps,
                config.min_edge_bps, volatility, config.target_volatility,
                config.volatility_cap,
            )
            if size.allowed <= 0:
                intents.append(TradeIntent(opp, Decimal(0), Decimal(0), quality.score,
                                            opp.net_edge_bps, False, size.reason))
                continue

            exposure = exposure_factory(opp, size.notional)
            risk = self.risk_gate.evaluate(
                exposure_ok=exposure.ok,
                drawdown_state=exposure.drawdown_state,
                net_edge_bps=opp.net_edge_bps,
                min_edge_bps=config.min_edge_bps,
            )
            intents.append(TradeIntent(
                opp, size.allowed, size.notional, quality.score,
                opp.net_edge_bps, risk.allow_trade, risk.reason,
            ))
        return sorted(intents, key=lambda x: x.net_edge_bps, reverse=True)

    @staticmethod
    def best_approved(intents):
        for intent in intents:
            if intent.approved and intent.quantity > 0:
                return intent
        return None
