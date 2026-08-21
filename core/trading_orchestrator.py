"""Coordinates validated opportunity, inventory, risk and paper execution."""
from dataclasses import dataclass
from decimal import Decimal
from execution.trade_state_machine import TradeState, TradeStateMachine

@dataclass(frozen=True)
class ExecutionResult:
    approved: bool
    reason: str
    state: TradeState
    pnl: Decimal = Decimal("0")

class TradingOrchestrator:
    def __init__(self, risk, inventory, execution):
        self.risk = risk
        self.inventory = inventory
        self.execution = execution

    def execute(self, opportunity, portfolio_state, timestamp_ms: int):
        sm = TradeStateMachine()
        sm.transition(TradeState.VALIDATED)
        notional = opportunity.quantity * opportunity.buy_price
        decision = self.risk.check(portfolio_state, notional)
        if not decision.approved:
            sm.transition(TradeState.CANCELLED)
            return ExecutionResult(False, decision.reason, sm.state)
        sm.transition(TradeState.LEG1_SUBMITTED)
        buy = self.execution.fill(opportunity.buy_venue, opportunity.symbol, "BUY", opportunity.quantity, opportunity.buy_price, timestamp_ms)
        sm.transition(TradeState.LEG1_FILLED)
        sm.transition(TradeState.LEG2_SUBMITTED)
        sell = self.execution.fill(opportunity.sell_venue, opportunity.symbol, "SELL", opportunity.quantity, opportunity.sell_price, timestamp_ms)
        sm.transition(TradeState.COMPLETED)
        pnl = (sell.price - buy.price) * opportunity.quantity - buy.fee - sell.fee
        return ExecutionResult(True, "completed", sm.state, pnl)
