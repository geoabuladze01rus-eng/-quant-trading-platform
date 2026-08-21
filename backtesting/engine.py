"""Deterministic event-driven backtesting primitives."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Iterable, Protocol

@dataclass(frozen=True)
class Bar:
    timestamp: datetime
    bid: Decimal
    ask: Decimal
    volume: Decimal = Decimal("0")

@dataclass(frozen=True)
class BacktestOrder:
    side: str
    quantity: Decimal
    limit_price: Decimal

@dataclass(frozen=True)
class BacktestFill:
    timestamp: datetime
    side: str
    quantity: Decimal
    price: Decimal
    fee: Decimal
    slippage: Decimal

class Strategy(Protocol):
    def on_bar(self, bar: Bar) -> BacktestOrder | None: ...

class BacktestEngine:
    """Uses bid/ask rather than candle close, with explicit fee and slippage."""
    def __init__(self, starting_cash: Decimal, fee_rate: Decimal, slippage_bps: Decimal) -> None:
        self.cash = starting_cash
        self.fee_rate = fee_rate
        self.slippage_bps = slippage_bps
        self.position = Decimal("0")
        self.fills: list[BacktestFill] = []

    def run(self, bars: Iterable[Bar], strategy: Strategy) -> list[BacktestFill]:
        for bar in bars:
            order = strategy.on_bar(bar)
            if order is None or order.quantity <= 0:
                continue
            if order.side == "BUY":
                if bar.ask > order.limit_price:
                    continue
                raw = bar.ask
                price = raw * (Decimal("1") + self.slippage_bps / Decimal("10000"))
                cash_delta = -(order.quantity * price)
                self.position += order.quantity
            elif order.side == "SELL":
                if bar.bid < order.limit_price:
                    continue
                raw = bar.bid
                price = raw * (Decimal("1") - self.slippage_bps / Decimal("10000"))
                cash_delta = order.quantity * price
                self.position -= order.quantity
            else:
                raise ValueError("side must be BUY or SELL")
            fee = abs(order.quantity * price) * self.fee_rate
            self.cash += cash_delta - fee
            self.fills.append(BacktestFill(bar.timestamp, order.side, order.quantity, price, fee, abs(price - raw)))
        return self.fills
