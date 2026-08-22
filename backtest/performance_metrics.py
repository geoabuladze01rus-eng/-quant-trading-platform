"""Performance and risk analytics for backtests and paper trading."""
from dataclasses import dataclass
from decimal import Decimal
from math import sqrt
@dataclass(frozen=True)
class PerformanceMetrics:
    total_return:Decimal; sharpe:Decimal; sortino:Decimal; max_drawdown:Decimal; profit_factor:Decimal; win_rate:Decimal; cagr:Decimal
class PerformanceAnalyzer:
    def analyze(self,equity:list[Decimal],periods_per_year:int=365)->PerformanceMetrics:
        if len(equity)<2:return PerformanceMetrics(Decimal(0),Decimal(0),Decimal(0),Decimal(0),Decimal(0),Decimal(0),Decimal(0))
        vals=[Decimal(str(x)) for x in equity]; start=vals[0]; end=vals[-1]; returns=[vals[i]/vals[i-1]-1 for i in range(1,len(vals)) if vals[i-1]!=0]
        avg=sum(returns,Decimal(0))/Decimal(len(returns)); var=sum((r-avg)**2 for r in returns)/Decimal(max(1,len(returns)-1)); sd=Decimal(str(sqrt(float(var))))
        downside=[r for r in returns if r<0]; dvar=sum((r*r for r in downside),Decimal(0))/Decimal(max(1,len(downside))); dsd=Decimal(str(sqrt(float(dvar))))
        sharpe=avg/sd*Decimal(str(sqrt(periods_per_year))) if sd else Decimal(0); sortino=avg/dsd*Decimal(str(sqrt(periods_per_year))) if dsd else Decimal(0)
        peak=start; mdd=Decimal(0)
        for v in vals: peak=max(peak,v); mdd=min(mdd,v/peak-1 if peak else Decimal(0))
        gains=sum((r for r in returns if r>0),Decimal(0)); losses=-sum((r for r in returns if r<0),Decimal(0)); pf=gains/losses if losses else (Decimal("999") if gains else Decimal(0)); win=Decimal(sum(r>0 for r in returns))/Decimal(len(returns)); years=Decimal(len(returns))/Decimal(periods_per_year); cagr=(end/start)**(Decimal(1)/years)-1 if start>0 and end>0 and years>0 else Decimal(0)
        return PerformanceMetrics(end/start-1,sharpe,sortino,mdd,pf,win,cagr)
