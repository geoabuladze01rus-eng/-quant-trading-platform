"""Hard daily-loss and portfolio drawdown circuit breaker."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
class GuardState(str,Enum): NORMAL="NORMAL"; WARNING="WARNING"; HALTED="HALTED"
@dataclass(frozen=True)
class GuardDecision:
    state:GuardState; allow_new_orders:bool; cancel_orders:bool; reason:str
class DrawdownGuard:
    def __init__(self,daily_loss_limit_pct=Decimal("2"),max_drawdown_pct=Decimal("10"),warning_pct=Decimal("1")):
        self.daily=Decimal(str(daily_loss_limit_pct)); self.max_dd=Decimal(str(max_drawdown_pct)); self.warning=Decimal(str(warning_pct))
    def evaluate(self,equity,day_start_equity,peak_equity)->GuardDecision:
        e=Decimal(str(equity)); d=Decimal(str(day_start_equity)); p=Decimal(str(peak_equity))
        if e<=0 or d<=0 or p<=0:return GuardDecision(GuardState.HALTED,False,True,"invalid_equity")
        daily_loss=max(Decimal(0),(d-e)/d*100); dd=max(Decimal(0),(p-e)/p*100)
        if daily_loss>=self.daily:return GuardDecision(GuardState.HALTED,False,True,"daily_loss_limit")
        if dd>=self.max_dd:return GuardDecision(GuardState.HALTED,False,True,"max_drawdown_limit")
        if daily_loss>=self.warning or dd>=self.warning:return GuardDecision(GuardState.WARNING,True,False,"risk_warning")
        return GuardDecision(GuardState.NORMAL,True,False,"OK")
