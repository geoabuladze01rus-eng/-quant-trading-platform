"""Exchange registry with health-aware deterministic venue selection."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
@dataclass(frozen=True)
class VenueSnapshot:
    venue:str; available_qty:Decimal; executable_price:Decimal; fee_bps:Decimal; healthy:bool=True
@dataclass(frozen=True)
class VenueChoice:
    venue:str; quantity:Decimal; effective_price:Decimal; score:Decimal
class ExchangeRegistry:
    def __init__(self): self._adapters:dict[str,Any]={}; self._health:dict[str,bool]={}
    def register(self,adapter:Any)->None: self._adapters[adapter.venue]=adapter; self._health.setdefault(adapter.venue,True)
    def set_health(self,venue:str,healthy:bool)->None:
        if venue not in self._adapters: raise KeyError(venue)
        self._health[venue]=healthy
    def is_healthy(self,venue:str)->bool: return self._health.get(venue,False)
    def get(self,venue:str)->Any: return self._adapters[venue]
    def _eligible(self,s:VenueSnapshot)->bool: return s.healthy and self.is_healthy(s.venue) and s.available_qty>0 and s.executable_price>0
    def choose_buy(self,snapshots:list[VenueSnapshot],quantity:Decimal)->VenueChoice|None:
        c=[]
        for s in snapshots:
            if not self._eligible(s): continue
            q=min(Decimal(str(quantity)),s.available_qty); p=s.executable_price*(Decimal(1)+s.fee_bps/Decimal(10000)); c.append(VenueChoice(s.venue,q,p,-p))
        return min(c,key=lambda x:x.effective_price) if c else None
    def choose_sell(self,snapshots:list[VenueSnapshot],quantity:Decimal)->VenueChoice|None:
        c=[]
        for s in snapshots:
            if not self._eligible(s): continue
            q=min(Decimal(str(quantity)),s.available_qty); p=s.executable_price*(Decimal(1)-s.fee_bps/Decimal(10000)); c.append(VenueChoice(s.venue,q,p,p))
        return max(c,key=lambda x:x.effective_price) if c else None
