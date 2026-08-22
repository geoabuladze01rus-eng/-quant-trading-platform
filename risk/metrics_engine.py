"""Risk-adjusted performance metrics for strategy and portfolio monitoring."""
from dataclasses import dataclass
from decimal import Decimal
from math import sqrt
@dataclass(frozen=True)
class RiskMetrics:
    mean:Decimal; volatility:Decimal; sharpe:Decimal; sortino:Decimal; max_drawdown:Decimal; profit_factor:Decimal; observations:int
class RiskMetricsEngine:
    def calculate(self,returns:list[Decimal],annualization=Decimal("365"),risk_free=Decimal("0"))->RiskMetrics:
        xs=[float(Decimal(str(x))) for x in returns]
        n=len(xs)
        if n<2:return RiskMetrics(Decimal(0),Decimal(0),Decimal(0),Decimal(0),Decimal(0),Decimal(0),n)
        mean=sum(xs)/n; var=sum((x-mean)**2 for x in xs)/(n-1); vol=sqrt(var); rf=float(risk_free); sharpe=((mean-rf)/vol*sqrt(float(annualization))) if vol else 0.0
        downside=[min(0.0,x-rf)**2 for x in xs]; dvol=sqrt(sum(downside)/(n-1)); sortino=((mean-rf)/dvol*sqrt(float(annualization))) if dvol else 0.0
        equity=1.0; peak=1.0; maxdd=0.0; gains=0.0; losses=0.0
        for x in xs:
            equity*=1+x; peak=max(peak,equity); maxdd=max(maxdd,(peak-equity)/peak); gains+=max(0,x); losses+=max(0,-x)
        pf=gains/losses if losses else (float("inf") if gains else 0.0)
        return RiskMetrics(Decimal(str(mean)),Decimal(str(vol)),Decimal(str(sharpe)),Decimal(str(sortino)),Decimal(str(maxdd)),Decimal(str(pf)),n)
