"""Lightweight Engle-Granger style residual-stationarity gate for pair selection."""
from dataclasses import dataclass
from math import log, sqrt


@dataclass(frozen=True)
class CointegrationResult:
    hedge_ratio:float; residual_mean:float; residual_std:float; half_life:float; stationary:bool; score:float
class CointegrationTester:
    def test(self,a:list[float],b:list[float],max_half_life:float=100.0,min_score:float=0.65)->CointegrationResult:
        if len(a)!=len(b) or len(a)<30: raise ValueError("insufficient_history")
        x=[log(v) for v in a]; y=[log(v) for v in b]; my=sum(y)/len(y); mx=sum(x)/len(x); var=sum((v-my)**2 for v in y)
        beta=sum((u-mx)*(v-my) for u,v in zip(x,y))/var if var else 0.0; r=[u-beta*v for u,v in zip(x,y)]; mr=sum(r)/len(r); sd=sqrt(sum((v-mr)**2 for v in r)/max(1,len(r)-1))
        dr=[r[i]-r[i-1] for i in range(1,len(r))]; lag=r[:-1]; lm=sum(lag)/len(lag); dm=sum(dr)/len(dr); den=sum((v-lm)**2 for v in lag); phi=sum((u-dm)*(v-lm) for u,v in zip(dr,lag))/den if den else 0.0
        hl=(-log(2)/phi) if phi<0 else float("inf"); mean_reversion=min(1.0,max(0.0,-phi*10)); volatility_score=1.0/(1.0+sd); score=0.7*mean_reversion+0.3*volatility_score; stationary=phi<0 and hl<=max_half_life and score>=min_score
        return CointegrationResult(beta,mr,sd,hl,stationary,score)
