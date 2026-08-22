"""Final portfolio-level risk gate before arbitrage execution."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
class RiskState(str,Enum): APPROVED="APPROVED"; WARNING="WARNING"; BLOCKED="BLOCKED"
@dataclass(frozen=True)
class PortfolioRiskState:
    state:RiskState; allow_trade:bool; reason:str; exposure_ok:bool; drawdown_ok:bool; edge_ok:bool
class PortfolioRiskAggregator:
    def evaluate(self,exposure_ok:bool,drawdown_state:str,net_edge_bps:Decimal,min_edge_bps:Decimal,metrics=None)->PortfolioRiskState:
        edge_ok=Decimal(str(net_edge_bps))>=Decimal(str(min_edge_bps))
        drawdown_ok=drawdown_state not in ("HALTED","BLOCKED")
        if not exposure_ok:return PortfolioRiskState(RiskState.BLOCKED,False,"exposure_limit",False,drawdown_ok,edge_ok)
        if not drawdown_ok:return PortfolioRiskState(RiskState.BLOCKED,False,"drawdown_guard",True,False,edge_ok)
        if not edge_ok:return PortfolioRiskState(RiskState.BLOCKED,False,"edge_below_threshold",True,True,False)
        if drawdown_state=="WARNING":return PortfolioRiskState(RiskState.WARNING,True,"risk_warning",True,True,True)
        return PortfolioRiskState(RiskState.APPROVED,True,"approved",True,True,True)
