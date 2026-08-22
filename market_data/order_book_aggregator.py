"""Depth-aware order book aggregation for executable cross-venue quotes."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable
@dataclass(frozen=True)
class Level:
    price:Decimal; quantity:Decimal
@dataclass(frozen=True)
class Book:
    venue:str; symbol:str; bids:tuple[Level,...]; asks:tuple[Level,...]; timestamp_ms:int
@dataclass(frozen=True)
class ExecutionQuote:
    venue:str; side:str; quantity:Decimal; average_price:Decimal; worst_price:Decimal; notional:Decimal; sufficient_liquidity:bool
class OrderBookAggregator:
    @staticmethod
    def executable(book:Book,side:str,quantity:Decimal)->ExecutionQuote:
        qty=Decimal(str(quantity)); levels=book.asks if side.upper()=="BUY" else book.bids; remaining=qty; notional=Decimal(0); worst=Decimal(0)
        for level in levels:
            take=min(remaining,level.quantity); notional+=take*level.price; remaining-=take; worst=level.price
            if remaining<=0: break
        filled=qty-remaining
        avg=notional/filled if filled>0 else Decimal(0)
        return ExecutionQuote(book.venue,side,filled,avg,worst,notional,remaining<=0)
    @staticmethod
    def best_executable(books:Iterable[Book],side:str,quantity:Decimal):
        quotes=[OrderBookAggregator.executable(b,side,quantity) for b in books]
        valid=[q for q in quotes if q.sufficient_liquidity]
        if not valid:return None
        return min(valid,key=lambda q:q.average_price) if side.upper()=="BUY" else max(valid,key=lambda q:q.average_price)
