"""Rule-based market regime detector used as a conservative strategy gate."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class MarketRegime(str,Enum): QUIET="QUIET"; TREND="TREND"; HIGH_VOL="HIGH_VOL"; STRESS="STRESS"; ILLIQUID="ILLIQUID"
@dataclass(frozen=True)
class RegimeSnapshot:
    realized_vol:Decimal; trend_strength:Decimal; spread_bps:Decimal; liquidity_score:Decimal; correlation:Decimal
@dataclass(frozen=True)
class RegimeDecision:
    regime:MarketRegime; confidence:Decimal; allow_arbitrage:bool; allow_new_risk:bool; reason:str
class MarketRegimeDetector:
    def classify(self,s:RegimeSnapshot)->RegimeDecision:
        vol=Decimal(str(s.realized_vol)); trend=Decimal(str(s.trend_strength)); spread=Decimal(str(s.spread_bps)); liq=Decimal(str(s.liquidity_score)); corr=abs(Decimal(str(s.correlation)))
        if liq<Decimal("0.3") or spread>Decimal(30): r=MarketRegime.ILLIQUID
        elif vol>=Decimal("0.08"): r=MarketRegime.STRESS
        elif vol>=Decimal("0.04"): r=MarketRegime.HIGH_VOL
        elif trend>=Decimal("0.7"): r=MarketRegime.TREND
        else: r=MarketRegime.QUIET
        confidence=min(Decimal(1),max(Decimal(0),(vol+trend+liq+corr)/Decimal(3)))
        allow=r!=MarketRegime.STRESS and r!=MarketRegime.ILLIQUID
        return RegimeDecision(r,confidence,allow,allow,r.value.lower())
