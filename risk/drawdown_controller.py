"""Portfolio drawdown circuit breaker with explicit operating states."""
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal
class RiskState(str,Enum): NORMAL="NORMAL"; CAUTION="CAUTION"; REDUCE_ONLY="REDUCE_ONLY"; HALT="HALT"
@dataclass(frozen=True)
class DrawdownPolicy:
    caution_pct:Decimal=Decimal("0.01"); reduce_only_pct:Decimal=Decimal("0.015"); halt_pct:Decimal=Decimal("0.02"); recovery_pct:Decimal=Decimal("0.005")
@dataclass(frozen=True)
class DrawdownDecision:
    state:RiskState; drawdown_pct:Decimal; allow_new_positions:bool; allow_reduce_only:bool; reason:str
class DrawdownController:
    def __init__(self,policy=DrawdownPolicy()): self.policy=policy; self.state=RiskState.NORMAL
    def evaluate(self,equity:Decimal,high_watermark:Decimal)->DrawdownDecision:
        equity=Decimal(str(equity)); high_watermark=Decimal(str(high_watermark))
        if high_watermark<=0: raise ValueError("high_watermark must be positive")
        dd=max(Decimal(0),(high_watermark-equity)/high_watermark); p=self.policy
        if dd>=p.halt_pct:self.state=RiskState.HALT
        elif dd>=p.reduce_only_pct:self.state=RiskState.REDUCE_ONLY
        elif dd>=p.caution_pct:self.state=RiskState.CAUTION
        elif dd<=p.recovery_pct:self.state=RiskState.NORMAL
        if self.state==RiskState.HALT:return DrawdownDecision(self.state,dd,False,False,"max_drawdown_reached")
        if self.state==RiskState.REDUCE_ONLY:return DrawdownDecision(self.state,dd,False,True,"reduce_only_mode")
        if self.state==RiskState.CAUTION:return DrawdownDecision(self.state,dd,True,True,"risk_caution")
        return DrawdownDecision(self.state,dd,True,True,"normal")
