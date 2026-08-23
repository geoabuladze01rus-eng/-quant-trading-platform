from __future__ import annotations
from dataclasses import dataclass
from ..arbitrage import ArbitrageOpportunity
from ..domain import OrderIntent, Side
from ..execution_group import ArbitrageExecutionGroup

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
            OrderIntent(opportunity.buy_venue, opportunity.symbol, Side.BUY, opportunity.quantity,
                        opportunity.buy_price, self.name, reason),
            OrderIntent(opportunity.sell_venue, opportunity.symbol, Side.SELL, opportunity.quantity,
                        opportunity.sell_price, self.name, reason),
        )

    def execution_group(self, opportunity: ArbitrageOpportunity) -> ArbitrageExecutionGroup:
        buy, sell = self.intents(opportunity)
        return ArbitrageExecutionGroup(buy=buy, sell=sell)
