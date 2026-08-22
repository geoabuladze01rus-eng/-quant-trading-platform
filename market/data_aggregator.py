"""Normalized multi-venue market-data aggregator."""
from dataclasses import dataclass
from decimal import Decimal
@dataclass(frozen=True)
class BookLevel:
    price:Decimal; quantity:Decimal
@dataclass(frozen=True)
class NormalizedBook:
    venue:str; symbol:str; timestamp_ms:int; bids:tuple[BookLevel,...]; asks:tuple[BookLevel,...]
class MarketDataAggregator:
    def __init__(self,max_age_ms:int=1000): self.max_age_ms=max_age_ms; self._books={}
    def update(self,book:NormalizedBook)->None: self._books[(book.venue,book.symbol)]=book
    def books(self,symbol:str,now_ms:int)->list[NormalizedBook]: return [b for b in self._books.values() if b.symbol==symbol and now_ms-b.timestamp_ms<=self.max_age_ms and b.bids and b.asks]
    def best_bid(self,symbol:str,now_ms:int):
        bs=self.books(symbol,now_ms); return max(((b.venue,b.bids[0]) for b in bs),key=lambda x:x[1].price,default=None)
    def best_ask(self,symbol:str,now_ms:int):
        bs=self.books(symbol,now_ms); return min(((b.venue,b.asks[0]) for b in bs),key=lambda x:x[1].price,default=None)
