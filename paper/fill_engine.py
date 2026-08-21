"""Deterministic paper fill engine for limit orders."""

from dataclasses import dataclass
from decimal import Decimal

from core.portfolio import Portfolio


@dataclass(frozen=True)
class PaperFill:
    symbol: str
    side: str
    quantity: Decimal
    price: Decimal
    fee: Decimal


class PaperFillEngine:
    def __init__(self, portfolio: Portfolio, fee_rate: Decimal = Decimal("0.0005")) -> None:
        self.portfolio = portfolio
        self.fee_rate = fee_rate

    def try_fill(self, *, symbol: str, side: str, quantity: Decimal, limit_price: Decimal, bid: Decimal, ask: Decimal) -> PaperFill | None:
        if quantity <= 0 or limit_price <= 0:
            return None
        if side == "BUY":
            if ask > limit_price:
                return None
            fill_price = ask
            cash_delta = -(quantity * fill_price)
        elif side == "SELL":
            if bid < limit_price:
                return None
            fill_price = bid
            cash_delta = quantity * fill_price
        else:
            raise ValueError("side must be BUY or SELL")

        fee = abs(quantity * fill_price) * self.fee_rate
        self.portfolio.cash += cash_delta - fee
        position = self.portfolio.positions.get(symbol)
        if position is None:
            from core.portfolio import Position
            position = Position(symbol=symbol)
            self.portfolio.positions[symbol] = position
        position.quantity += quantity if side == "BUY" else -quantity
        position.mark_price = fill_price
        return PaperFill(symbol, side, quantity, fill_price, fee)
