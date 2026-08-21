"""Deterministic execution simulator: latency, spread, slippage and partial fills."""
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class OrderBookSnapshot:
    bid: Decimal
    ask: Decimal
    bid_qty: Decimal
    ask_qty: Decimal
    timestamp_ms: int

@dataclass(frozen=True)
class SimulatedFill:
    requested_qty: Decimal
    filled_qty: Decimal
    average_price: Decimal
    fee: Decimal
    slippage_bps: Decimal
    latency_ms: int

class RealisticExecutionSimulator:
    def __init__(self, fee_bps: Decimal = Decimal("10"), latency_ms: int = 50):
        self.fee_bps = fee_bps
        self.latency_ms = latency_ms

    def execute(self, side: str, quantity: Decimal, book: OrderBookSnapshot, now_ms: int) -> SimulatedFill:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if book.ask <= book.bid or book.bid <= 0:
            raise ValueError("invalid order book")
        side = side.upper()
        if side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")
        available = book.ask_qty if side == "BUY" else book.bid_qty
        filled = min(quantity, available)
        price = book.ask if side == "BUY" else book.bid
        mid = (book.bid + book.ask) / Decimal("2")
        slippage_bps = abs(price - mid) / mid * Decimal("10000")
        notional = filled * price
        fee = notional * self.fee_bps / Decimal("10000")
        return SimulatedFill(quantity, filled, price, fee, slippage_bps, self.latency_ms)
