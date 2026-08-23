"""Canonical atomic representation of a two-leg arbitrage execution group."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from .domain import OrderIntent

@dataclass(frozen=True, slots=True)
class ArbitrageExecutionGroup:
    """Two correlated legs that must pass risk as one operation."""
    buy: OrderIntent
    sell: OrderIntent

    def __post_init__(self) -> None:
        if self.buy.side.value != "buy" or self.sell.side.value != "sell":
            raise ValueError("arbitrage group requires BUY and SELL legs")
        if self.buy.symbol != self.sell.symbol:
            raise ValueError("arbitrage legs must use the same symbol")
        if self.buy.quantity <= 0 or self.sell.quantity <= 0:
            raise ValueError("arbitrage quantities must be positive")
        if self.buy.quantity != self.sell.quantity:
            raise ValueError("arbitrage legs must use equal quantities")
        if self.buy.venue == self.sell.venue:
            raise ValueError("inter-exchange arbitrage requires distinct venues")

    @property
    def quantity(self) -> Decimal:
        return self.buy.quantity

    @property
    def notional(self) -> Decimal:
        buy_price = self.buy.limit_price or Decimal("0")
        sell_price = self.sell.limit_price or Decimal("0")
        return self.quantity * (buy_price + sell_price)

    @property
    def expected_gross_edge(self) -> Decimal:
        buy_price = self.buy.limit_price or Decimal("0")
        sell_price = self.sell.limit_price or Decimal("0")
        if buy_price <= 0:
            return Decimal("0")
        return (sell_price - buy_price) / buy_price * Decimal("10000")
