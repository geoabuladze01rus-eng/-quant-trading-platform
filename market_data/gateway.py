"""Venue-normalized market-data gateway with stale-feed detection."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Quote:
    venue:str; symbol:str; bid:Decimal; ask:Decimal; bid_qty:Decimal; ask_qty:Decimal; timestamp_ms:int
@dataclass(frozen=True)
class GatewayStatus:
    healthy:bool; reason:str; age_ms:int
class MarketDataGateway:
    def __init__(self,stale_after_ms:int=1500): self.stale_after_ms=stale_after_ms; self._quotes={}
    def update(self,q:Quote)->None:
        if q.bid<=0 or q.ask<=0 or q.bid>q.ask: raise ValueError("invalid_quote")
        self._quotes[(q.venue,q.symbol)]=q
    def quote(self,venue:str,symbol:str): return self._quotes.get((venue,symbol))
    def status(self,venue:str,symbol:str,now_ms:int)->GatewayStatus:
        q=self.quote(venue,symbol)
        if q is None:return GatewayStatus(False,"missing_feed",0)
        age=max(0,int(now_ms)-q.timestamp_ms)
        return GatewayStatus(age<=self.stale_after_ms,"stale_feed" if age>self.stale_after_ms else "OK",age)
    def best_cross_venue(self,symbol:str):
        quotes=[q for (v,s),q in self._quotes.items() if s==symbol]
        return min(quotes,key=lambda q:q.ask).venue,max(quotes,key=lambda q:q.bid).venue if quotes else (None,None)
