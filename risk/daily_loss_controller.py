"""Daily loss and drawdown controller for new-position gating."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class RiskState(str,Enum): ACTIVE="ACTIVE"; WARNING="WARNING"; RISK_OFF="RISK_OFF"
@dataclass(frozen=True)
class RiskDecision:
    state:RiskState; daily_loss:Decimal; drawdown:Decimal; allow_new_positions:bool; reason:str
class DailyLossController:
    def __init__(self,max_daily_loss_pct:Decimal=Decimal(2),warning_pct:Decimal=Decimal(1),max_drawdown_pct:Decimal=Decimal(10)):
        self.max_daily_loss_pct=Decimal(str(max_daily_loss_pct)); self.warning_pct=Decimal(str(warning_pct)); self.max_drawdown_pct=Decimal(str(max_drawdown_pct))
    def evaluate(self,day_start_equity:Decimal,current_equity:Decimal,high_watermark:Decimal)->RiskDecision:
        start=Decimal(str(day_start_equity)); current=Decimal(str(current_equity)); high=Decimal(str(high_watermark))
        if start<=0 or high<=0:return RiskDecision(RiskState.RISK_OFF,Decimal(0),Decimal(0),False,"invalid_equity")
        loss=max(Decimal(0),(start-current)/start*100); dd=max(Decimal(0),(high-current)/high*100)
        if loss>=self.max_daily_loss_pct or dd>=self.max_drawdown_pct:return RiskDecision(RiskState.RISK_OFF,loss,dd,False,"risk_limit_reached")
        if loss>=self.warning_pct:return RiskDecision(RiskState.WARNING,loss,dd,True,"daily_loss_warning")
        return RiskDecision(RiskState.ACTIVE,loss,dd,True,"OK")
