"""Statistical arbitrage pair model using rolling spread and z-score."""
from dataclasses import dataclass
from decimal import Decimal
from math import log, sqrt


@dataclass(frozen=True)
class PairSignal:
    symbol_a:str; symbol_b:str; hedge_ratio:Decimal; zscore:Decimal; action:str; confidence:Decimal
class StatisticalPairs:
    def fit(self,prices_a:list[Decimal],prices_b:list[Decimal],lookback:int=100,entry_z:Decimal=Decimal(2),exit_z:Decimal=Decimal("0.5"))->PairSignal:
        if len(prices_a)<lookback or len(prices_b)<lookback: raise ValueError("insufficient_history")
        a=[log(float(x)) for x in prices_a[-lookback:]]; b=[log(float(x)) for x in prices_b[-lookback:]]; mb=sum(b)/len(b); ma=sum(a)/len(a); cov=sum((x-ma)*(y-mb) for x,y in zip(a,b)); var=sum((y-mb)**2 for y in b)
        beta=cov/var if var else 0.0; spread=[x-beta*y for x,y in zip(a,b)]; ms=sum(spread)/len(spread); sd=sqrt(sum((x-ms)**2 for x in spread)/max(1,len(spread)-1)); z=(spread[-1]-ms)/sd if sd else 0.0
        action="ENTER_LONG_SPREAD" if z<=-float(entry_z) else "ENTER_SHORT_SPREAD" if z>=float(entry_z) else "EXIT" if abs(z)<=float(exit_z) else "HOLD"
        confidence=min(Decimal(1),abs(Decimal(str(z)))/Decimal(str(entry_z)))
        return PairSignal("A","B",Decimal(str(beta)),Decimal(str(z)),action,confidence)
