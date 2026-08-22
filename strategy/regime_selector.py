"""Market-regime-aware strategy selector with explicit safety fallback."""
from dataclasses import dataclass
from enum import Enum
class Regime(str,Enum): CALM="CALM"; TREND="TREND"; HIGH_VOL="HIGH_VOL"; STRESS="STRESS"; UNKNOWN="UNKNOWN"
@dataclass(frozen=True)
class RegimeFeatures: volatility:float; trend_strength:float; liquidity_score:float; anomaly_score:float
@dataclass(frozen=True)
class StrategyChoice: regime:Regime; strategy:str; enabled:bool; reason:str
class RegimeSelector:
    def classify(self,f:RegimeFeatures)->Regime:
        if f.liquidity_score<=0 or f.anomaly_score>=0.9:return Regime.STRESS
        if f.volatility>=0.08:return Regime.HIGH_VOL
        if f.trend_strength>=0.65:return Regime.TREND
        if f.volatility<0.03 and f.anomaly_score<0.4:return Regime.CALM
        return Regime.UNKNOWN
    def select(self,f:RegimeFeatures)->StrategyChoice:
        r=self.classify(f)
        if r==Regime.STRESS:return StrategyChoice(r,"NONE",False,"risk_off")
        if r==Regime.HIGH_VOL:return StrategyChoice(r,"cross_exchange",True,"prefer_short_horizon")
        if r==Regime.TREND:return StrategyChoice(r,"statistical_arb",True,"trend_filtered")
        if r==Regime.CALM:return StrategyChoice(r,"triangular",True,"stable_microstructure")
        return StrategyChoice(r,"NONE",False,"insufficient_regime_confidence")
