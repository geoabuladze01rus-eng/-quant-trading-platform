"""Fuse market, macro and news signals into a bounded regime-risk score."""
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class FusionInput:
    volatility: Decimal
    liquidity: Decimal
    spread_bps: Decimal
    news_impact: str
    news_confidence: Decimal
    macro_impact: str

@dataclass(frozen=True)
class FusionResult:
    risk_score: Decimal
    regime: str
    position_multiplier: Decimal
    allow_new_trades: bool
    reasons: tuple[str, ...]

class EventFusionEngine:
    IMPACT={"LOW":Decimal("0.10"),"MEDIUM":Decimal("0.30"),"HIGH":Decimal("0.60"),"CRITICAL":Decimal("1.00")}
    def evaluate(self,x):
        if not 0<=x.liquidity<=1 or not 0<=x.news_confidence<=1: raise ValueError("invalid normalized input")
        score=min(Decimal("1"),x.volatility*Decimal("5")+(1-x.liquidity)*Decimal("0.25")+min(x.spread_bps/Decimal("100"),Decimal("1"))*Decimal("0.20")+self.IMPACT.get(x.news_impact,Decimal("0"))*x.news_confidence+self.IMPACT.get(x.macro_impact,Decimal("0"))*Decimal("0.50"))
        if score>=Decimal("0.80"): return FusionResult(score,"STRESS",Decimal("0"),False,("composite_risk_high",))
        if score>=Decimal("0.55"): return FusionResult(score,"HIGH_RISK",Decimal("0.25"),True,("composite_risk_elevated",))
        if score>=Decimal("0.30"): return FusionResult(score,"CAUTION",Decimal("0.50"),True,("composite_risk_caution",))
        return FusionResult(score,"NORMAL",Decimal("1.00"),True,("composite_risk_normal",))
