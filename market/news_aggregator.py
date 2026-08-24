"""Provider-agnostic news aggregator: deduplication, source weighting and signal confidence."""
import hashlib
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class NewsItem:
    source:str; title:str; published_ms:int; sentiment:Decimal; impact:Decimal
@dataclass(frozen=True)
class NewsSignal:
    key:str; sentiment:Decimal; impact:Decimal; confidence:Decimal; sources:int
class NewsAggregator:
    def aggregate(self,items:list[NewsItem])->list[NewsSignal]:
        groups={}
        for item in items:
            key=hashlib.sha256(item.title.strip().lower().encode()).hexdigest()[:16]
            groups.setdefault(key,[]).append(item)
        out=[]
        for key,group in groups.items():
            weights={"official":Decimal("1.5"),"reuters":Decimal("1.4"),"bloomberg":Decimal("1.4")}
            total=sum((weights.get(x.source.lower(),Decimal(1)) for x in group),Decimal(0))
            sentiment=sum((x.sentiment*weights.get(x.source.lower(),Decimal(1)) for x in group),Decimal(0))/total
            impact=sum((x.impact*weights.get(x.source.lower(),Decimal(1)) for x in group),Decimal(0))/total
            confidence=min(Decimal(1),Decimal(len(group))/Decimal(3))
            out.append(NewsSignal(key,sentiment,impact,confidence,len(group)))
        return out
