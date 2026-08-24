"""Backtest performance metrics from realized trade P&L."""
from dataclasses import dataclass
from decimal import Decimal
from math import sqrt


@dataclass(frozen=True)
class BacktestMetrics:
    total_pnl: Decimal
    trades: int
    wins: int
    losses: int
    win_rate: Decimal
    profit_factor: Decimal
    max_drawdown: Decimal
    sharpe: Decimal
    sortino: Decimal

class MetricsCalculator:
    @staticmethod
    def calculate(pnls, initial_equity=Decimal(100000)):
        xs=[Decimal(str(x)) for x in pnls]
        if initial_equity <= 0: raise ValueError("initial_equity must be positive")
        if not xs: return BacktestMetrics(Decimal(0),0,0,0,Decimal(0),Decimal(0),Decimal(0),Decimal(0),Decimal(0))
        equity=Decimal(str(initial_equity)); peak=equity; max_dd=Decimal(0); wins=sum(x>0 for x in xs); losses=sum(x<0 for x in xs)
        for x in xs:
            equity += x; peak=max(peak,equity); max_dd=max(max_dd,(peak-equity)/peak)
        gross_profit=sum((x for x in xs if x>0),Decimal(0)); gross_loss=-sum((x for x in xs if x<0),Decimal(0))
        mean=sum(xs,Decimal(0))/len(xs); variance=sum(((x-mean)**2 for x in xs),Decimal(0))/len(xs); downside=sum((min(x,Decimal(0))**2 for x in xs),Decimal(0))/len(xs)
        sharpe=mean/Decimal(str(sqrt(float(variance))))*Decimal(str(sqrt(len(xs)))) if variance else Decimal(0)
        sortino=mean/Decimal(str(sqrt(float(downside))))*Decimal(str(sqrt(len(xs)))) if downside else Decimal(0)
        pf=gross_profit/gross_loss if gross_loss else Decimal("Infinity")
        return BacktestMetrics(sum(xs,Decimal(0)),len(xs),wins,losses,Decimal(wins)/len(xs),pf,max_dd,sharpe,sortino)
