"""Append-only decision audit trail for deterministic trading decisions."""
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DecisionEvent:
    event_id:str; timestamp_ms:int; strategy_id:str; symbol:str; action:str; reason:str; inputs:dict[str,Any]
class DecisionLogger:
    def __init__(self): self._events={}
    def record(self,event:DecisionEvent)->None:
        if event.event_id not in self._events:self._events[event.event_id]=event
    def get(self,event_id:str): return self._events.get(event_id)
    def events(self): return tuple(self._events.values())
