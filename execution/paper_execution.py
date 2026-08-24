"""Deterministic paper execution and portfolio accounting."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

Side = Literal["BUY", "SELL"]
@dataclass(frozen=True)
class Fill:
    venue: str
    symbol: str
    side: Side
    quantity: Decimal
    price: Decimal
    fee: Decimal
    timestamp_ms: int
@dataclass
class PaperPortfolio:
    cash: Decimal
    base_position: Decimal = Decimal(0)
    realized_pnl: Decimal = Decimal(0)
    fees_paid: Decimal = Decimal(0)
    def apply(self, fill: Fill) -> None:
        notional = fill.quantity * fill.price
        if fill.side == "BUY":
            self.cash -= notional + fill.fee
            self.base_position += fill.quantity
        else:
            self.cash += notional - fill.fee
            self.base_position -= fill.quantity
        self.fees_paid += fill.fee
    def mark_to_market(self, price: Decimal) -> Decimal:
        return self.cash + self.base_position * price
class PaperExecutionEngine:
    def __init__(self, portfolio: PaperPortfolio, fee_bps: Decimal = Decimal(10)) -> None:
        self.portfolio = portfolio
        self.fee_bps = fee_bps
    def fill(self, venue: str, symbol: str, side: Side, quantity: Decimal, price: Decimal, timestamp_ms: int) -> Fill:
        if quantity <= 0 or price <= 0:
            raise ValueError("quantity and price must be positive")
        fee = quantity * price * self.fee_bps / Decimal(10000)
        result = Fill(venue, symbol, side, quantity, price, fee, timestamp_ms)
        self.portfolio.apply(result)
        return result
