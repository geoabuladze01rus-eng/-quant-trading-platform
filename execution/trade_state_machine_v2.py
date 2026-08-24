from dataclasses import dataclass
from enum import Enum
from typing import ClassVar


class TradeState(str, Enum):
    SIGNAL="SIGNAL"; RISK_CHECK="RISK_CHECK"; RESERVED="RESERVED"; BUY_SUBMITTED="BUY_SUBMITTED"; BUY_PARTIAL="BUY_PARTIAL"; BUY_FILLED="BUY_FILLED"; SELL_SUBMITTED="SELL_SUBMITTED"; SELL_PARTIAL="SELL_PARTIAL"; SELL_FILLED="SELL_FILLED"; RECONCILE="RECONCILE"; HEDGE="HEDGE"; COMPLETE="COMPLETE"; FAILED="FAILED"; KILLED="KILLED"

@dataclass
class TradeContext:
    state: TradeState=TradeState.SIGNAL
    buy_filled: bool=False
    sell_filled: bool=False
    error: str|None=None

class TradeStateMachine:
    ALLOWED: ClassVar[dict[TradeState, set[TradeState]]] = {
        TradeState.SIGNAL:{TradeState.RISK_CHECK,TradeState.KILLED},
        TradeState.RISK_CHECK:{TradeState.RESERVED,TradeState.FAILED,TradeState.KILLED},
        TradeState.RESERVED:{TradeState.BUY_SUBMITTED,TradeState.FAILED,TradeState.KILLED},
        TradeState.BUY_SUBMITTED:{TradeState.BUY_PARTIAL,TradeState.BUY_FILLED,TradeState.FAILED,TradeState.KILLED},
        TradeState.BUY_PARTIAL:{TradeState.BUY_PARTIAL,TradeState.BUY_FILLED,TradeState.FAILED,TradeState.HEDGE,TradeState.KILLED},
        TradeState.BUY_FILLED:{TradeState.SELL_SUBMITTED,TradeState.HEDGE,TradeState.KILLED},
        TradeState.SELL_SUBMITTED:{TradeState.SELL_PARTIAL,TradeState.SELL_FILLED,TradeState.FAILED,TradeState.HEDGE,TradeState.KILLED},
        TradeState.SELL_PARTIAL:{TradeState.SELL_PARTIAL,TradeState.SELL_FILLED,TradeState.HEDGE,TradeState.KILLED},
        TradeState.SELL_FILLED:{TradeState.RECONCILE},TradeState.RECONCILE:{TradeState.COMPLETE,TradeState.HEDGE,TradeState.FAILED},TradeState.HEDGE:{TradeState.RECONCILE,TradeState.FAILED,TradeState.KILLED},TradeState.COMPLETE:set(),TradeState.FAILED:set(),TradeState.KILLED:set()}
    def __init__(self): self.context=TradeContext()
    def transition(self,target,error=None):
        if target not in self.ALLOWED[self.context.state]: raise ValueError(f"invalid transition {self.context.state} -> {target}")
        self.context.state=target
        if error: self.context.error=error
        return self.context
