"""News intelligence: classify event impact/direction/confidence without issuing trade orders."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import ClassVar


class Direction(str,Enum): UNKNOWN="UNKNOWN"; BULLISH="BULLISH"; BEARISH="BEARISH"; MIXED="MIXED"
@dataclass(frozen=True)
class NewsSignal: event_id:str; impact:str; direction:Direction; confidence:Decimal; topics:tuple[str,...]
class NewsIntelligence:
    KEYWORDS: ClassVar[dict[str, tuple[str, Direction]]] = {"rate_hike":("HIGH",Direction.BEARISH),"rate_cut":("HIGH",Direction.BULLISH),"inflation_hot":("HIGH",Direction.BEARISH),"inflation_cool":("MEDIUM",Direction.BULLISH),"etf_approval":("HIGH",Direction.BULLISH),"regulatory_ban":("CRITICAL",Direction.BEARISH),"exchange_hack":("CRITICAL",Direction.BEARISH)}
    def classify(self,event_id,topics,confidence):
        confidence=Decimal(str(confidence))
        if not 0<=confidence<=1: raise ValueError("confidence must be 0..1")
        hits=[self.KEYWORDS[t] for t in topics if t in self.KEYWORDS]
        if not hits:return NewsSignal(event_id,"LOW",Direction.UNKNOWN,confidence,tuple(topics))
        ranks={"LOW":0,"MEDIUM":1,"HIGH":2,"CRITICAL":3}; impact=max(hits,key=lambda x:ranks[x[0]])[0]
        dirs={h[1] for h in hits}; direction=next(iter(dirs)) if len(dirs)==1 else Direction.MIXED
        return NewsSignal(event_id,impact,direction,confidence,tuple(topics))
