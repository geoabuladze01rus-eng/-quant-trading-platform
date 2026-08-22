"""Append-only normalized PnL ledger and audit events."""
from dataclasses import dataclass
from decimal import Decimal
@dataclass(frozen=True)
class PnLEvent:
    event_id:str; timestamp_ms:int; strategy_id:str; venue:str; symbol:str; realized_pnl:Decimal; fee:Decimal; slippage:Decimal; event_type:str
class PnLLedger:
    def __init__(self): self._events={}
    def append(self,event:PnLEvent)->None:
        if event.event_id in self._events: return
        self._events[event.event_id]=event
    def events(self): return tuple(self._events.values())
    def realized_pnl(self)->Decimal: return sum((e.realized_pnl for e in self._events.values()),Decimal(0))
    def total_fees(self)->Decimal: return sum((e.fee for e in self._events.values()),Decimal(0))
    def total_slippage(self)->Decimal: return sum((e.slippage for e in self._events.values()),Decimal(0))
    def net_pnl(self)->Decimal: return self.realized_pnl()-self.total_fees()-self.total_slippage()
