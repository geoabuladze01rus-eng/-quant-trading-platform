"""Exchange registry and deterministic venue selection for executable orders."""
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
    def __init__(self): self._adapters:dict[str,Any]={}
    def register(self,adapter:Any)->None: self._adapters[adapter.venue]=adapter
    def get(self,venue:str)->Any: return self._adapters[venue]
    def choose_buy(self,snapshots:list[VenueSnapshot],quantity:Decimal)->VenueChoice|None:
        candidates=[]
        for s in snapshots:
            if not s.healthy or s.available_qty<=0 or s.executable_price<=0: continue
            qty=min(Decimal(str(quantity)),s.available_qty); effective=s.executable_price*(Decimal(1)+s.fee_bps/Decimal(10000)); candidates.append(VenueChoice(s.venue,qty,effective,-effective))
        return min(candidates,key=lambda x:x.effective_price) if candidates else None
    def choose_sell(self,snapshots:list[VenueSnapshot],quantity:Decimal)->VenueChoice|None:
        candidates=[]
        for s in snapshots:
            if not s.healthy or s.available_qty<=0 or s.executable_price<=0: continue
            qty=min(Decimal(str(quantity)),s.available_qty); effective=s.executable_price*(Decimal(1)-s.fee_bps/Decimal(10000)); candidates.append(VenueChoice(s.venue,qty,effective,effective))
        return max(candidates,key=lambda x:x.effective_price) if candidates else None
