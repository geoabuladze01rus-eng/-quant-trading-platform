"""Fail-safe state machine for two-leg arbitrage execution."""
from enum import Enum

class TradeState(str, Enum):
    NEW = "NEW"
    VALIDATED = "VALIDATED"
    LEG1_SUBMITTED = "LEG1_SUBMITTED"
    LEG1_PARTIAL = "LEG1_PARTIAL"
    LEG1_FILLED = "LEG1_FILLED"
    LEG2_SUBMITTED = "LEG2_SUBMITTED"
    COMPLETED = "COMPLETED"
    HEDGE_REQUIRED = "HEDGE_REQUIRED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"

_ALLOWED = {
    TradeState.NEW: {TradeState.VALIDATED, TradeState.CANCELLED},
    TradeState.VALIDATED: {TradeState.LEG1_SUBMITTED, TradeState.CANCELLED},
    TradeState.LEG1_SUBMITTED: {TradeState.LEG1_PARTIAL, TradeState.LEG1_FILLED, TradeState.HEDGE_REQUIRED, TradeState.FAILED},
    TradeState.LEG1_PARTIAL: {TradeState.LEG1_SUBMITTED, TradeState.LEG1_FILLED, TradeState.HEDGE_REQUIRED, TradeState.FAILED},
    TradeState.LEG1_FILLED: {TradeState.LEG2_SUBMITTED, TradeState.HEDGE_REQUIRED, TradeState.FAILED},
    TradeState.LEG2_SUBMITTED: {TradeState.COMPLETED, TradeState.HEDGE_REQUIRED, TradeState.FAILED},
    TradeState.HEDGE_REQUIRED: {TradeState.COMPLETED, TradeState.FAILED},
    TradeState.COMPLETED: set(), TradeState.CANCELLED: set(), TradeState.FAILED: set(),
}

class TradeStateMachine:
    def __init__(self): self.state = TradeState.NEW
    def transition(self, target: TradeState) -> TradeState:
        if target not in _ALLOWED[self.state]:
            raise ValueError(f"invalid transition: {self.state} -> {target}")
        self.state = target
        return self.state
