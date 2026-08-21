"""Exchange-agnostic real-time market-data health layer."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
class FeedState(str,Enum): DISCONNECTED="DISCONNECTED"; CONNECTING="CONNECTING"; LIVE="LIVE"; STALE="STALE"; RESYNC="RESYNC"
@dataclass(frozen=True)
class MarketTick: venue:str; symbol:str; sequence:int; timestamp_ms:int; bid:Decimal; ask:Decimal
@dataclass(frozen=True)
class FeedHealth: state:FeedState; last_sequence:int; age_ms:int; gap_detected:bool
class MarketDataHealth:
    def __init__(self,max_age_ms=500): self.max_age_ms=max_age_ms; self.sequence=0; self.state=FeedState.DISCONNECTED
    def on_tick(self,tick:MarketTick,now_ms:int)->FeedHealth:
        gap=tick.sequence!=self.sequence+1 if self.sequence else False; self.sequence=tick.sequence; age=max(0,now_ms-tick.timestamp_ms); self.state=FeedState.RESYNC if gap else (FeedState.STALE if age>self.max_age_ms else FeedState.LIVE); return FeedHealth(self.state,self.sequence,age,gap)
    def disconnected(self)->FeedHealth: self.state=FeedState.DISCONNECTED; return FeedHealth(self.state,self.sequence,0,False)
