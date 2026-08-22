"""Depth-aware historical execution for two-leg arbitrage backtests."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable
@dataclass(frozen=True)
class Level:
    price:Decimal; quantity:Decimal
@dataclass(frozen=True)
class DepthSnapshot:
    timestamp_ms:int; venue:str; symbol:str; bids:tuple[Level,...]; asks:tuple[Level,...]
@dataclass(frozen=True)
class DepthFill:
    requested:Decimal; filled:Decimal; notional:Decimal; average_price:Decimal; complete:bool
class DepthExecutor:
    @staticmethod
    def execute(levels:Iterable[Level],requested:Decimal,ascending:bool)->DepthFill:
        remaining=Decimal(str(requested)); filled=Decimal(0); notional=Decimal(0)
        ordered=sorted(levels,key=lambda x:Decimal(str(x.price)),reverse=not ascending)
        for level in ordered:
            if remaining<=0:break
            px=Decimal(str(level.price)); qty=min(remaining,Decimal(str(level.quantity))); filled+=qty; notional+=qty*px; remaining-=qty
        avg=notional/filled if filled else Decimal(0)
        return DepthFill(Decimal(str(requested)),filled,notional,avg,remaining<=0)
    @staticmethod
    def arbitrage(buy:DepthSnapshot,sell:DepthSnapshot,requested:Decimal)->tuple[DepthFill,DepthFill]:
        return DepthExecutor.execute(buy.asks,requested,True),DepthExecutor.execute(sell.bids,requested,False)
