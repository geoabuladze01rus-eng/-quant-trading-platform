"""Two-leg arbitrage execution state machine. Paper-safe: no exchange API calls."""
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal

class ExecutionState(str, Enum):
    NEW = "NEW"
    BUY_PENDING = "BUY_PENDING"
    SELL_PENDING = "SELL_PENDING"
    HEDGING = "HEDGING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

@dataclass
class ExecutionContext:
    quantity: Decimal
    buy_filled: Decimal = Decimal("0")
    sell_filled: Decimal = Decimal("0")
    state: ExecutionState = ExecutionState.NEW

class ArbitrageExecution:
    def __init__(self, ctx: ExecutionContext) -> None:
        self.ctx = ctx

    def start(self) -> ExecutionState:
        self.ctx.state = ExecutionState.BUY_PENDING if self.ctx.quantity > 0 else ExecutionState.FAILED
        return self.ctx.state

    def buy_ack(self, filled: Decimal) -> ExecutionState:
        if self.ctx.state != ExecutionState.BUY_PENDING or filled < 0 or filled > self.ctx.quantity:
            self.ctx.state = ExecutionState.FAILED
            return self.ctx.state
        self.ctx.buy_filled = filled
        self.ctx.state = ExecutionState.SELL_PENDING if filled == self.ctx.quantity else ExecutionState.HEDGING
        return self.ctx.state

    def sell_ack(self, filled: Decimal) -> ExecutionState:
        if self.ctx.state not in (ExecutionState.SELL_PENDING, ExecutionState.HEDGING) or filled < 0:
            self.ctx.state = ExecutionState.FAILED
            return self.ctx.state
        self.ctx.sell_filled = min(filled, self.ctx.quantity)
        if self.ctx.buy_filled == self.ctx.sell_filled == self.ctx.quantity:
            self.ctx.state = ExecutionState.COMPLETED
        elif self.ctx.buy_filled != self.ctx.sell_filled:
            self.ctx.state = ExecutionState.HEDGING
        return self.ctx.state

    def timeout(self) -> ExecutionState:
        if self.ctx.state in (ExecutionState.BUY_PENDING, ExecutionState.SELL_PENDING):
            self.ctx.state = ExecutionState.HEDGING
        return self.ctx.state

    def fail(self) -> ExecutionState:
        self.ctx.state = ExecutionState.FAILED
        return self.ctx.state
