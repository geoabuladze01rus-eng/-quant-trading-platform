"""Idempotent order-intent registry preventing duplicate leg submissions."""
from dataclasses import dataclass
from enum import Enum


class IntentStatus(str,Enum): NEW="NEW"; SUBMITTED="SUBMITTED"; FILLED="FILLED"; CANCELLED="CANCELLED"; FAILED="FAILED"
@dataclass(frozen=True)
class OrderIntent:
    intent_id:str; strategy_id:str; leg_id:str; status:IntentStatus; exchange_order_id:str|None=None
class IdempotencyRegistry:
    def __init__(self): self._items={}
    def reserve(self,intent_id:str,strategy_id:str,leg_id:str)->OrderIntent:
        existing=self._items.get(intent_id)
        if existing is not None:return existing
        item=OrderIntent(intent_id,strategy_id,leg_id,IntentStatus.NEW); self._items[intent_id]=item; return item
    def transition(self,intent_id:str,status:IntentStatus,exchange_order_id:str|None=None)->OrderIntent:
        current=self._items.get(intent_id)
        if current is None: raise KeyError("unknown_intent")
        item=OrderIntent(current.intent_id,current.strategy_id,current.leg_id,status,exchange_order_id or current.exchange_order_id); self._items[intent_id]=item; return item
    def get(self,intent_id:str): return self._items.get(intent_id)
