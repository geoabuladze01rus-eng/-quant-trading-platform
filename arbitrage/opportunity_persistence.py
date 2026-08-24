"""Track persistence and confirmation rate of arbitrage opportunities."""
from collections import deque
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class PersistenceStats:
    observations:int; confirmations:int; confirmation_rate:Decimal; age_ms:int; stable:bool
class OpportunityPersistence:
    def __init__(self,max_samples:int=100): self._events=deque(maxlen=max_samples); self._first=None; self._last=None
    def observe(self,timestamp_ms:int,net_edge_bps:Decimal,min_edge_bps:Decimal)->PersistenceStats:
        ts=int(timestamp_ms); edge=Decimal(str(net_edge_bps)); self._events.append(edge); self._first=ts if self._first is None else self._first; self._last=ts
        confirmations=sum(1 for x in self._events if x>=Decimal(str(min_edge_bps))); n=len(self._events); rate=Decimal(confirmations)/Decimal(n) if n else Decimal(0)
        return PersistenceStats(n,confirmations,rate,ts-self._first,rate>=Decimal("0.6"))
    def reset(self): self._events.clear(); self._first=None; self._last=None
