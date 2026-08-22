"""Portfolio-wide exposure aggregation across venues, assets and strategies."""
from dataclasses import dataclass
from decimal import Decimal
@dataclass(frozen=True)
class Exposure:
    venue:str; asset:str; strategy:str; notional:Decimal
@dataclass(frozen=True)
class ExposureCheck:
    allowed:bool; current:Decimal; projected:Decimal; limit:Decimal; reason:str
class PortfolioExposure:
    def __init__(self): self._items={}
    def set(self,key:str,exposure:Exposure)->None: self._items[key]=exposure
    def total(self)->Decimal: return sum((e.notional for e in self._items.values()),Decimal(0))
    def aggregate(self,field:str,value:str)->Decimal: return sum((e.notional for e in self._items.values() if getattr(e,field)==value),Decimal(0))
    def check(self,additional:Exposure,max_total:Decimal,max_asset:Decimal,max_strategy:Decimal,max_venue:Decimal)->ExposureCheck:
        current=self.total(); projected=current+additional.notional; asset=self.aggregate("asset",additional.asset)+additional.notional; strategy=self.aggregate("strategy",additional.strategy)+additional.notional; venue=self.aggregate("venue",additional.venue)+additional.notional
        limits=(("portfolio",projected,max_total),("asset",asset,max_asset),("strategy",strategy,max_strategy),("venue",venue,max_venue))
        for name,value,limit in limits:
            if value>Decimal(str(limit)): return ExposureCheck(False,current,projected,Decimal(str(limit)),name+"_limit")
        return ExposureCheck(True,current,projected,Decimal(str(max_total)),"approved")
