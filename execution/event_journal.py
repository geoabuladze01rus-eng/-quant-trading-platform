"""Durable-style event journal abstraction with idempotent event application."""
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class JournalRecord:
    event_id:str; sequence:int; payload:Any
class EventJournal:
    def __init__(self): self._records=[]; self._seen=set()
    def append_once(self,event_id:str,payload:Any)->JournalRecord|None:
        if event_id in self._seen:return None
        record=JournalRecord(event_id,len(self._records)+1,payload); self._records.append(record); self._seen.add(event_id); return record
    def replay(self,handler:Callable[[Any],None])->None:
        for record in self._records: handler(record.payload)
    def contains(self,event_id:str)->bool:return event_id in self._seen
    def records(self):return tuple(self._records)
