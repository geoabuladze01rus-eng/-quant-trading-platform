"""Paper liquidity and partial-fill simulator."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

Side = Literal["BUY", "SELL"]
@dataclass(frozen=True)
class LiquiditySnapshot:
    bid_price: Decimal
    ask_price: Decimal
    bid_size: Decimal
    ask_size: Decimal
    timestamp_ms: int
@dataclass(frozen=True)
class SimulatedFill:
    quantity: Decimal
    price: Decimal
    filled: bool
    reason: str
class LiquiditySimulator:
    def __init__(self, partial_fill_ratio: Decimal = Decimal(1)) -> None:
        if not (Decimal(0) < partial_fill_ratio <= Decimal(1)):
            raise ValueError("partial_fill_ratio must be in (0, 1]")
        self.partial_fill_ratio = partial_fill_ratio
    def execute(self, book: LiquiditySnapshot, side: Side, requested_qty: Decimal) -> SimulatedFill:
        if requested_qty <= 0:
            return SimulatedFill(Decimal(0), Decimal(0), False, "invalid_quantity")
        available = book.ask_size if side == "BUY" else book.bid_size
        price = book.ask_price if side == "BUY" else book.bid_price
        if available <= 0 or price <= 0:
            return SimulatedFill(Decimal(0), Decimal(0), False, "no_liquidity")
        qty = min(requested_qty, available * self.partial_fill_ratio)
        return SimulatedFill(qty, price, qty == requested_qty, "filled" if qty == requested_qty else "partial_fill")
