"""Feed health monitor: freshness, heartbeat and latency gates."""
from dataclasses import dataclass


@dataclass(frozen=True)
class FeedHealth:
    venue:str; connected:bool; fresh:bool; latency_ms:int; healthy:bool; reason:str
class FeedHealthMonitor:
    def __init__(self,max_latency_ms:int=250,max_stale_ms:int=1000): self.max_latency_ms=max_latency_ms; self.max_stale_ms=max_stale_ms
    def evaluate(self,venue:str,connected:bool,last_message_age_ms:int,latency_ms:int)->FeedHealth:
        fresh=last_message_age_ms<=self.max_stale_ms; latency_ok=latency_ms<=self.max_latency_ms; healthy=connected and fresh and latency_ok
        reason="OK" if healthy else ",".join(x for x,y in (("DISCONNECTED",not connected),("STALE",not fresh),("HIGH_LATENCY",not latency_ok)) if y)
        return FeedHealth(venue,connected,fresh,latency_ms,healthy,reason)
