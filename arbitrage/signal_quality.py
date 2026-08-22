"""Reject fragile or stale arbitrage signals before risk/execution."""
from dataclasses import dataclass
from decimal import Decimal
@dataclass(frozen=True)
class SignalQuality:
    approved:bool; score:Decimal; reason:str
class SignalQualityFilter:
    def evaluate(self,age_ms:int,max_age_ms:int,spread_bps:Decimal,max_spread_bps:Decimal,net_edge_bps:Decimal,min_edge_bps:Decimal,edge_observations:int,min_observations:int,book_imbalance:Decimal,max_imbalance:Decimal)->SignalQuality:
        if age_ms>max_age_ms:return SignalQuality(False,Decimal(0),"stale_market_data")
        if spread_bps<=0 or spread_bps>max_spread_bps:return SignalQuality(False,Decimal(0),"abnormal_spread")
        if net_edge_bps<min_edge_bps:return SignalQuality(False,Decimal(0),"weak_net_edge")
        if edge_observations<min_observations:return SignalQuality(False,Decimal(0),"unstable_opportunity")
        if abs(book_imbalance)>max_imbalance:return SignalQuality(False,Decimal(0),"orderbook_anomaly")
        score=min(Decimal(100),Decimal(100)*net_edge_bps/(max(min_edge_bps,Decimal("0.0001"))*2))
        return SignalQuality(True,score,"approved")
