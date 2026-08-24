"""Estimate opportunity survival under execution latency and edge decay."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class DecayInput:
    edge_bps:Decimal; decay_bps_per_ms:Decimal; round_trip_latency_ms:int; safety_margin_bps:Decimal
@dataclass(frozen=True)
class DecayForecast:
    expected_remaining_edge_bps:Decimal; survival_ratio:Decimal; executable:bool; reason:str
class OpportunityDecayEngine:
    def forecast(self,x:DecayInput)->DecayForecast:
        edge=Decimal(str(x.edge_bps)); decay=Decimal(str(x.decay_bps_per_ms)); latency=Decimal(x.round_trip_latency_ms); margin=Decimal(str(x.safety_margin_bps)); remaining=edge-decay*latency-margin; ratio=max(Decimal(0),min(Decimal(1),remaining/max(edge,Decimal("0.000001")))); ok=remaining>0
        return DecayForecast(remaining,ratio,ok,"ready" if ok else "edge_decays_before_execution")
