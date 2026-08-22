"""Finite-state execution controller for multi-leg arbitrage."""
from enum import Enum
from dataclasses import dataclass
class State(str,Enum): SEARCH="SEARCH"; ENTER="ENTER"; PARTIAL="PARTIAL"; HEDGE="HEDGE"; EXIT="EXIT"; HALT="HALT"
@dataclass(frozen=True)
class Transition:
    state:State; reason:str
class ExecutionStateMachine:
    def __init__(self): self.state=State.SEARCH
    def event(self,event:str)->Transition:
        e=event.upper()
        table={(State.SEARCH,"SIGNAL"):State.ENTER,(State.ENTER,"PARTIAL_FILL"):State.PARTIAL,(State.ENTER,"FILLED"):State.EXIT,(State.PARTIAL,"RESIDUAL"):State.HEDGE,(State.PARTIAL,"FILLED"):State.EXIT,(State.HEDGE,"HEDGED"):State.EXIT,(State.EXIT,"CLOSED"):State.SEARCH,(State.SEARCH,"RISK_HALT"):State.HALT,(State.ENTER,"RISK_HALT"):State.HALT,(State.PARTIAL,"RISK_HALT"):State.HALT,(State.HEDGE,"RISK_HALT"):State.HALT}
        new=table.get((self.state,e))
        if new is None:return Transition(self.state,"ignored:"+e)
        self.state=new; return Transition(new,e)
