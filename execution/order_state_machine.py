"""Deterministic order lifecycle state machine."""
from enum import Enum
class OrderState(str,Enum): NEW="NEW"; SUBMITTED="SUBMITTED"; PARTIAL="PARTIAL"; FILLED="FILLED"; CANCELLED="CANCELLED"; FAILED="FAILED"; HEDGED="HEDGED"
_TRANSITIONS={OrderState.NEW:{OrderState.SUBMITTED,OrderState.FAILED},OrderState.SUBMITTED:{OrderState.PARTIAL,OrderState.FILLED,OrderState.CANCELLED,OrderState.FAILED},OrderState.PARTIAL:{OrderState.PARTIAL,OrderState.FILLED,OrderState.CANCELLED,OrderState.FAILED,OrderState.HEDGED},OrderState.FAILED:{OrderState.HEDGED},OrderState.CANCELLED:{OrderState.HEDGED},OrderState.FILLED:set(),OrderState.HEDGED:set()}
class OrderStateMachine:
    def __init__(self): self._states={}
    def state(self,order_id): return self._states.get(order_id,OrderState.NEW)
    def transition(self,order_id,next_state):
        current=self.state(order_id)
        if next_state not in _TRANSITIONS[current]: raise ValueError(f"invalid transition: {current}->{next_state}")
        self._states[order_id]=next_state
        return next_state
