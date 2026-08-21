"""Hard portfolio exposure guard evaluated immediately before order submission."""
from dataclasses import dataclass
from decimal import Decimal
@dataclass(frozen=True)
class ExposureSnapshot:
    portfolio_notional:Decimal; asset_notional:Decimal; venue_notional:Decimal; strategy_notional:Decimal; daily_loss:Decimal
@dataclass(frozen=True)
class ExposureLimits:
    max_portfolio:Decimal; max_asset:Decimal; max_venue:Decimal; max_strategy:Decimal; max_daily_loss:Decimal
@dataclass(frozen=True)
class GuardDecision:
    allowed:bool; reason:str; projected_portfolio:Decimal; projected_asset:Decimal; projected_venue:Decimal; projected_strategy:Decimal
class ExposureGuard:
    def check(self,snapshot:ExposureSnapshot,limits:ExposureLimits,additional_notional:Decimal)->GuardDecision:
        n=Decimal(str(additional_notional)); p=snapshot.portfolio_notional+n; a=snapshot.asset_notional+n; v=snapshot.venue_notional+n; s=snapshot.strategy_notional+n; loss=Decimal(str(snapshot.daily_loss))
        checks=((p<=limits.max_portfolio,"portfolio_limit"),(a<=limits.max_asset,"asset_limit"),(v<=limits.max_venue,"venue_limit"),(s<=limits.max_strategy,"strategy_limit"),(loss<=limits.max_daily_loss,"daily_loss_limit"))
        for ok,reason in checks:
            if not ok:return GuardDecision(False,reason,p,a,v,s)
        return GuardDecision(True,"approved",p,a,v,s)
