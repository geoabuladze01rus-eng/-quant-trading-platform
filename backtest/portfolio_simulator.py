"""Portfolio-level state simulator for historical arbitrage results."""
from dataclasses import dataclass
from decimal import Decimal
@dataclass(frozen=True)
class EquityPoint:
    timestamp_ms:int; equity:Decimal; pnl:Decimal; drawdown:Decimal
@dataclass(frozen=True)
class PortfolioBacktestResult:
    initial_equity:Decimal; final_equity:Decimal; net_pnl:Decimal; max_drawdown:Decimal; points:tuple[EquityPoint,...]
class PortfolioSimulator:
    def __init__(self,initial_equity=Decimal("100000")):
        self.initial=Decimal(str(initial_equity))
    def run(self,trades)->PortfolioBacktestResult:
        equity=self.initial; peak=equity; max_dd=Decimal(0); points=[]
        for trade in sorted(trades,key=lambda x:x.timestamp_ms):
            equity+=Decimal(str(trade.net)); peak=max(peak,equity); dd=(peak-equity)/peak if peak else Decimal(0); max_dd=max(max_dd,dd)
            points.append(EquityPoint(trade.timestamp_ms,equity,equity-self.initial,dd))
        return PortfolioBacktestResult(self.initial,equity,equity-self.initial,max_dd,tuple(points))
