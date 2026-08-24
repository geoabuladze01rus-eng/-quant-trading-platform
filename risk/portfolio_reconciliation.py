"""Independent reconciliation of internal state against exchange-reported state."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class AssetBalance:
    asset: str
    free: Decimal
    locked: Decimal

@dataclass(frozen=True)
class Position:
    symbol: str
    quantity: Decimal

@dataclass(frozen=True)
class ReconciliationResult:
    balanced: bool
    balance_diffs: dict
    position_diffs: dict
    order_ids_missing_internal: tuple[str,...]
    order_ids_missing_exchange: tuple[str,...]
    reasons: tuple[str,...]

class PortfolioReconciler:
    def __init__(self,tolerance=Decimal("0.00000001")): self.tolerance=Decimal(str(tolerance))
    def reconcile(self,internal_balances,exchange_balances,internal_positions,exchange_positions,internal_order_ids,exchange_order_ids):
        ib={x.asset:x.free+x.locked for x in internal_balances}; eb={x.asset:x.free+x.locked for x in exchange_balances}
        bd={a:eb.get(a,Decimal(0))-ib.get(a,Decimal(0)) for a in set(ib)|set(eb) if abs(eb.get(a,Decimal(0))-ib.get(a,Decimal(0)))>self.tolerance}
        ip={x.symbol:x.quantity for x in internal_positions}; ep={x.symbol:x.quantity for x in exchange_positions}
        pd={s:ep.get(s,Decimal(0))-ip.get(s,Decimal(0)) for s in set(ip)|set(ep) if abs(ep.get(s,Decimal(0))-ip.get(s,Decimal(0)))>self.tolerance}
        mi=tuple(sorted(set(exchange_order_ids)-set(internal_order_ids))); me=tuple(sorted(set(internal_order_ids)-set(exchange_order_ids))); reasons=[]
        if bd: reasons.append("balance_mismatch")
        if pd: reasons.append("position_mismatch")
        if mi or me: reasons.append("order_mismatch")
        return ReconciliationResult(not reasons,bd,pd,mi,me,tuple(reasons))
