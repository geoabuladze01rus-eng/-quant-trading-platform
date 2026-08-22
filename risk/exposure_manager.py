"""Portfolio exposure limits by asset, venue, strategy and correlated group."""
from dataclasses import dataclass
from decimal import Decimal
@dataclass(frozen=True)
class Exposure:
    asset:str; venue:str; strategy:str; notional:Decimal; group:str|None=None
@dataclass(frozen=True)
class ExposureDecision:
    allowed:bool; reason:str; total:Decimal; asset_total:Decimal; venue_total:Decimal; strategy_total:Decimal; group_total:Decimal
class ExposureManager:
    def check(self,current:list[Exposure],candidate:Exposure,max_total,max_asset,max_venue,max_strategy,max_group)->ExposureDecision:
        def D(x): return Decimal(str(x))
        total=sum((D(x.notional) for x in current),Decimal(0)); asset=sum((D(x.notional) for x in current if x.asset==candidate.asset),Decimal(0)); venue=sum((D(x.notional) for x in current if x.venue==candidate.venue),Decimal(0)); strategy=sum((D(x.notional) for x in current if x.strategy==candidate.strategy),Decimal(0)); group=sum((D(x.notional) for x in current if candidate.group and x.group==candidate.group),Decimal(0)); n=D(candidate.notional)
        limits=[(total+n,D(max_total),"portfolio_limit"),(asset+n,D(max_asset),"asset_limit"),(venue+n,D(max_venue),"venue_limit"),(strategy+n,D(max_strategy),"strategy_limit"),(group+n,D(max_group),"correlation_group_limit")]
        for value,limit,reason in limits:
            if value>limit:return ExposureDecision(False,reason,total,asset,venue,strategy,group)
        return ExposureDecision(True,"approved",total,asset,venue,strategy,group)
