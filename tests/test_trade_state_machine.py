import pytest

from execution.trade_state_machine import TradeState, TradeStateMachine


def test_normal_two_leg_flow():
    sm = TradeStateMachine()
    sm.transition(TradeState.VALIDATED)
    sm.transition(TradeState.LEG1_SUBMITTED)
    sm.transition(TradeState.LEG1_FILLED)
    sm.transition(TradeState.LEG2_SUBMITTED)
    sm.transition(TradeState.COMPLETED)
    assert sm.state == TradeState.COMPLETED

def test_invalid_transition_is_rejected():
    sm = TradeStateMachine()
    with pytest.raises(ValueError):
        sm.transition(TradeState.LEG2_SUBMITTED)

def test_hedge_path_exists():
    sm = TradeStateMachine()
    sm.transition(TradeState.VALIDATED)
    sm.transition(TradeState.LEG1_SUBMITTED)
    sm.transition(TradeState.HEDGE_REQUIRED)
    sm.transition(TradeState.COMPLETED)
    assert sm.state == TradeState.COMPLETED
