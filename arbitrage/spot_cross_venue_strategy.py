"""Deterministic spot cross-venue arbitrage signal generation."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ArbitrageSignal:
    symbol:str; buy_venue:str; sell_venue:str; quantity:Decimal; gross_edge_bps:Decimal; net_edge_bps:Decimal; executable:bool; reason:str
class SpotCrossVenueStrategy:
    def __init__(self,min_net_edge_bps:Decimal=Decimal(2)): self.min_net_edge_bps=Decimal(str(min_net_edge_bps))
    def evaluate(self,symbol:str,buy_venue:str,buy_price:Decimal,sell_venue:str,sell_price:Decimal,quantity:Decimal,buy_fee_bps:Decimal,sell_fee_bps:Decimal,slippage_bps:Decimal)->ArbitrageSignal:
        q=Decimal(str(quantity)); bp=Decimal(str(buy_price)); sp=Decimal(str(sell_price)); fees=Decimal(str(buy_fee_bps))+Decimal(str(sell_fee_bps)); gross=(sp/bp-1)*Decimal(10000) if bp>0 else Decimal(0); net=gross-fees-Decimal(str(slippage_bps)); ok=q>0 and net>=self.min_net_edge_bps
        return ArbitrageSignal(symbol,buy_venue,sell_venue,q,gross,net,ok,"approved" if ok else "insufficient_net_edge")
