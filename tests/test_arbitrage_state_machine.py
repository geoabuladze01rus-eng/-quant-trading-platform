from decimal import Decimal
from execution.arbitrage_state_machine import ArbitrageExecution, ExecutionContext, ExecutionState

def test_full_two_leg_flow():
    ex = ArbitrageExecution(ExecutionContext(Decimal("1")))
    assert ex.start() == ExecutionState.BUY_PENDING
    assert ex.buy_ack(Decimal("1")) == ExecutionState.SELL_PENDING
    assert ex.sell_ack(Decimal("1")) == ExecutionState.COMPLETED

def test_partial_fill_enters_hedging():
    ex = ArbitrageExecution(ExecutionContext(Decimal("1")))
    ex.start()
    assert ex.buy_ack(Decimal("0.4")) == ExecutionState.HEDGING

def test_timeout_enters_hedging():
    ex = ArbitrageExecution(ExecutionContext(Decimal("1")))
    ex.start()
    assert ex.timeout() == ExecutionState.HEDGING

def test_invalid_quantity_fails_closed():
    ex = ArbitrageExecution(ExecutionContext(Decimal("0")))
    assert ex.start() == ExecutionState.FAILED
