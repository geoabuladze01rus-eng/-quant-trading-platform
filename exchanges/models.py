"""Normalized multi-exchange account models."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class OrderSide(str, Enum):
    BUY="BUY"; SELL="SELL"
class OrderStatus(str, Enum):
    NEW="NEW"; PARTIALLY_FILLED="PARTIALLY_FILLED"; FILLED="FILLED"; CANCELED="CANCELED"; REJECTED="REJECTED"
@dataclass(frozen=True)
class NormalizedBalance:
    venue:str; asset:str; free:Decimal; locked:Decimal
@dataclass(frozen=True)
class NormalizedPosition:
    venue:str; symbol:str; quantity:Decimal; entry_price:Decimal; unrealized_pnl:Decimal
@dataclass(frozen=True)
class NormalizedOrder:
    venue:str; order_id:str; client_order_id:str; symbol:str; side:OrderSide; quantity:Decimal; filled_quantity:Decimal; price:Decimal|None; status:OrderStatus; fee:Decimal; fee_asset:str; timestamp_ms:int
