"""Normalized Binance, Bybit and OKX order-book adapter contract."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class BookLevel: price:Decimal; quantity:Decimal
@dataclass(frozen=True)
class NormalizedOrderBook:
    venue:str; symbol:str; sequence:int; timestamp_ms:int; bids:tuple; asks:tuple
class BaseAdapter:
    venue="BASE"
    def normalize_symbol(self,s): return s.replace("-","/").replace("_","/").upper()
    def levels(self,rows): return tuple(BookLevel(Decimal(str(x[0])),Decimal(str(x[1]))) for x in rows if Decimal(str(x[1]))>0)
class BinanceAdapter(BaseAdapter):
    venue="BINANCE"
    def parse(self,p): return NormalizedOrderBook(self.venue,self.normalize_symbol(p["symbol"]),int(p.get("lastUpdateId",0)),int(p.get("E",0)),self.levels(p.get("bids",[])),self.levels(p.get("asks",[])))
class BybitAdapter(BaseAdapter):
    venue="BYBIT"
    def parse(self,p):
        d=p.get("data",p); return NormalizedOrderBook(self.venue,self.normalize_symbol(d.get("s",d.get("symbol",""))),int(d.get("u",d.get("seq",0))),int(d.get("ts",0)),self.levels(d.get("b",d.get("bids",[]))),self.levels(d.get("a",d.get("asks",[]))))
class OKXAdapter(BaseAdapter):
    venue="OKX"
    def parse(self,p):
        d=(p.get("data") or [{}])[0]; return NormalizedOrderBook(self.venue,self.normalize_symbol(d.get("instId",d.get("symbol",""))),int(d.get("seqId",d.get("seq",0))),int(d.get("ts",0)),self.levels(d.get("bids",[])),self.levels(d.get("asks",[])))
