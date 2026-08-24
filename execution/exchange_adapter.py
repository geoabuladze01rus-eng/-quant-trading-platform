"""Venue-neutral exchange adapter contract and normalized market/order models."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Protocol


class OrderSide(str,Enum): BUY="BUY"; SELL="SELL"
class OrderType(str,Enum): LIMIT="LIMIT"; MARKET="MARKET"
@dataclass(frozen=True)
class NormalizedOrder:
    client_order_id:str; symbol:str; side:OrderSide; order_type:OrderType; quantity:Decimal; price:Decimal|None=None
@dataclass(frozen=True)
class NormalizedOrderResult:
    exchange_order_id:str; status:str; filled_qty:Decimal; avg_price:Decimal|None
class ExchangeAdapter(Protocol):
    venue:str
    async def submit(self,order:NormalizedOrder)->NormalizedOrderResult: ...
    async def cancel(self,exchange_order_id:str)->bool: ...
    async def order_status(self,exchange_order_id:str)->NormalizedOrderResult: ...
    async def health(self)->bool: ...
class UnsupportedExchangeAdapter:
    def __init__(self,venue:str): self.venue=venue
    async def submit(self,order): raise NotImplementedError(f"{self.venue} adapter not configured")
    async def cancel(self,exchange_order_id): raise NotImplementedError
    async def order_status(self,exchange_order_id): raise NotImplementedError
    async def health(self): return False
class BinanceAdapter(UnsupportedExchangeAdapter):
    def __init__(self): super().__init__("binance")
class BybitAdapter(UnsupportedExchangeAdapter):
    def __init__(self): super().__init__("bybit")
class OKXAdapter(UnsupportedExchangeAdapter):
    def __init__(self): super().__init__("okx")
