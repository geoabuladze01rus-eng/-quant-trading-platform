"""Venue-agnostic exchange adapter contract and normalized order models."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
class Side(str,Enum): BUY="BUY"; SELL="SELL"
class OrderStatus(str,Enum): NEW="NEW"; PARTIALLY_FILLED="PARTIALLY_FILLED"; FILLED="FILLED"; CANCELED="CANCELED"; REJECTED="REJECTED"; EXPIRED="EXPIRED"
@dataclass(frozen=True)
class OrderRequest:
    symbol:str; side:Side; quantity:Decimal; price:Decimal|None=None; client_order_id:str|None=None
@dataclass(frozen=True)
class OrderSnapshot:
    venue:str; order_id:str; client_order_id:str; symbol:str; side:Side; requested:Decimal; filled:Decimal; average_price:Decimal; status:OrderStatus; timestamp_ms:int
class ExchangeAdapter(ABC):
    @property
    @abstractmethod
    def venue(self)->str:...
    @abstractmethod
    async def place_order(self,request:OrderRequest)->OrderSnapshot:...
    @abstractmethod
    async def cancel_order(self,order_id:str)->OrderSnapshot:...
    @abstractmethod
    async def get_order(self,order_id:str)->OrderSnapshot:...
    @abstractmethod
    async def get_balance(self,asset:str)->Decimal:...
    @abstractmethod
    async def health(self)->bool:...
