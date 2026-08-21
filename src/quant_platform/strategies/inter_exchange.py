from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ..arbitrage import ArbitrageOpportunity
from ..domain import OrderIntent, Side


@dataclass(frozen=True, slots=True)
class InterExchangeArbitrageStrategy:
    name: str = "inter_exchange_arbitrage"

    def intents(self, opportunity: ArbitrageOpportunity) -> tuple[OrderIntent, OrderIntent]:
        reason = (
            f"net_edge={opportunity.net_edge_bps}bps; "
            f"buy={opportunity.buy_venue.value}@{opportunity.buy_price}; "
            f"sell={opportunity.sell_venue.value}@{opportunity.sell_price}"
        )
        return (
            OrderIntent(
                venue=opportunity.buy_venue,
                symbol=opportunity.symbol,
                side=Side.BUY,
                quantity=opportunity.quantity,
                limit_price=opportunity.buy_price,
                strategy=self.name,
                reason=reason,
            ),
            OrderIntent(
                venue=opportunity.sell_venue,
                symbol=opportunity.symbol,
                side=Side.SELL,
                quantity=opportunity.quantity,
                limit_price=opportunity.sell_price,
                strategy=self.name,
                reason=reason,
            ),
        )
