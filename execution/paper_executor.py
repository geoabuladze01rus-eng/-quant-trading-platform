"""Deterministic paper executor: no real exchange orders are sent."""
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from time import time_ns


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

@dataclass(frozen=True)
class PaperOrder:
    order_id: str
    symbol: str
    side: Side
    quantity: Decimal
    price: Decimal
    timestamp_ns: int

@dataclass
class PaperPortfolio:
    cash: Decimal
    positions: dict[str, Decimal] = field(default_factory=dict)
    realized_pnl: Decimal = Decimal(0)

class PaperExecutor:
    def __init__(self, initial_cash: Decimal):
        self.portfolio = PaperPortfolio(initial_cash)
        self.orders: list[PaperOrder] = []
        self._seq = 0

    def execute(self, symbol: str, side: Side, quantity: Decimal, price: Decimal) -> PaperOrder:
        if quantity <= 0 or price <= 0:
            raise ValueError("quantity and price must be positive")
        notional = quantity * price
        position = self.portfolio.positions.get(symbol, Decimal(0))
        if side is Side.BUY:
            if notional > self.portfolio.cash:
                raise ValueError("insufficient paper cash")
            self.portfolio.cash -= notional
            self.portfolio.positions[symbol] = position + quantity
        else:
            if quantity > position:
                raise ValueError("insufficient paper position")
            self.portfolio.cash += notional
            self.portfolio.positions[symbol] = position - quantity
        self._seq += 1
        order = PaperOrder(f"paper-{self._seq}", symbol, side, quantity, price, time_ns())
        self.orders.append(order)
        return order
