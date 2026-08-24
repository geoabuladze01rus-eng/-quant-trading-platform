"""Event-driven cross-venue arbitrage backtester with explicit costs."""
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class BacktestEvent:
    timestamp_ms:int; buy_price:Decimal; sell_price:Decimal; quantity:Decimal
@dataclass(frozen=True)
class BacktestTrade:
    timestamp_ms:int; quantity:Decimal; gross:Decimal; fees:Decimal; slippage:Decimal; net:Decimal
@dataclass(frozen=True)
class BacktestResult:
    trades:tuple[BacktestTrade,...]; net_pnl:Decimal; win_rate:Decimal; total_trades:int
class BacktestEngine:
    def __init__(self,fee_bps=Decimal(10),slippage_bps=Decimal(0),min_edge_bps=None):
        self.fee_bps=Decimal(str(fee_bps)); self.slippage_bps=Decimal(str(slippage_bps)); self.min_edge_bps=None if min_edge_bps is None else Decimal(str(min_edge_bps))
    def run(self,events:Iterable[BacktestEvent],signal:Callable[[BacktestEvent],bool]|None=None)->BacktestResult:
        trades=[]
        for e in events:
            buy=Decimal(str(e.buy_price)); sell=Decimal(str(e.sell_price)); q=Decimal(str(e.quantity))
            if buy<=0 or sell<=0 or q<=0: continue
            edge=(sell-buy)/buy*Decimal(10000)
            if (self.min_edge_bps is not None and edge<self.min_edge_bps) or (signal and not signal(e)): continue
            gross=(sell-buy)*q; fees=(buy+sell)*q*self.fee_bps/Decimal(10000); slip=(buy+sell)*q*self.slippage_bps/Decimal(10000)
            trades.append(BacktestTrade(e.timestamp_ms,q,gross,fees,slip,gross-fees-slip))
        pnl=sum((t.net for t in trades),Decimal(0)); wins=sum(1 for t in trades if t.net>0); n=len(trades)
        return BacktestResult(tuple(trades),pnl,Decimal(wins)/Decimal(n) if n else Decimal(0),n)
