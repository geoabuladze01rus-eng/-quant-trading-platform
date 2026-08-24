"""Deterministic paper execution simulator for safe pre-live testing."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class PaperOrder:
    order_id: str
    venue: str
    side: str
    price: Decimal
    quantity: Decimal
    fee_bps: Decimal = Decimal(10)
    slippage_bps: Decimal = Decimal(5)

@dataclass(frozen=True)
class PaperFill:
    order_id: str
    filled_price: Decimal
    filled_quantity: Decimal
    fee: Decimal

class PaperExecutionEngine:
    def __init__(self):
        self.orders: dict[str, PaperOrder] = {}
        self.fills: list[PaperFill] = []

    def submit(self, order: PaperOrder) -> None:
        if order.order_id in self.orders: raise ValueError("duplicate order id")
        if order.quantity <= 0 or order.price <= 0: raise ValueError("invalid order")
        if order.side not in {"BUY", "SELL"}: raise ValueError("side must be BUY or SELL")
        self.orders[order.order_id] = order

    def fill(self, order_id: str, quantity: Decimal, market_price: Decimal) -> PaperFill:
        order = self.orders[order_id]
        if quantity <= 0 or quantity > order.quantity: raise ValueError("invalid fill quantity")
        if market_price <= 0: raise ValueError("invalid market price")
        direction = Decimal(1) if order.side == "BUY" else Decimal(-1)
        filled_price = market_price * (Decimal(1) + direction * order.slippage_bps / Decimal(10000))
        fee = filled_price * quantity * order.fee_bps / Decimal(10000)
        fill = PaperFill(order_id, filled_price, quantity, fee)
        self.fills.append(fill)
        return fill
