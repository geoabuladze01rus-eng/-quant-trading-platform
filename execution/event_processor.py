"""Normalize exchange order events into deterministic execution lifecycle updates."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class OrderEvent(str,Enum): NEW="NEW"; PARTIALLY_FILLED="PARTIALLY_FILLED"; FILLED="FILLED"; CANCELED="CANCELED"; REJECTED="REJECTED"; EXPIRED="EXPIRED"
@dataclass(frozen=True)
class ExecutionEvent:
    venue:str; order_id:str; client_order_id:str; event:OrderEvent; cumulative_filled:Decimal; last_fill:Decimal; timestamp_ms:int
@dataclass(frozen=True)
class EventDecision:
    accepted:bool; action:str; state:str; reason:str
class OrderEventProcessor:
    def __init__(self): self._last_cumulative={}
    def process(self,event:ExecutionEvent)->EventDecision:
        previous=self._last_cumulative.get(event.client_order_id,Decimal(0)); current=Decimal(str(event.cumulative_filled))
        if current<previous:return EventDecision(False,"IGNORE","UNKNOWN","non_monotonic_fill")
        self._last_cumulative[event.client_order_id]=current
        if event.event==OrderEvent.NEW:return EventDecision(True,"TRACK","EXECUTING","order_accepted")
        if event.event==OrderEvent.PARTIALLY_FILLED:return EventDecision(True,"RECONCILE","RECONCILING","partial_fill")
        if event.event==OrderEvent.FILLED:return EventDecision(True,"RECONCILE","RECONCILING","filled")
        if event.event in (OrderEvent.CANCELED,OrderEvent.EXPIRED):return EventDecision(True,"RECONCILE","RECONCILING","order_closed_with_residual_check")
        if event.event==OrderEvent.REJECTED:return EventDecision(True,"HEDGE_OR_HALT","HEDGING","order_rejected")
        return EventDecision(False,"IGNORE","UNKNOWN","unsupported_event")
