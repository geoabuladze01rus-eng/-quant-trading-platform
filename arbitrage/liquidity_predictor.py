"""Short-horizon liquidity and slippage predictor for execution gating."""
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class LiquiditySnapshot:
    venue: str
    symbol: str
    depth_notional: Decimal
    spread_bps: Decimal
    update_age_ms: int
    trade_rate: Decimal

@dataclass(frozen=True)
class LiquidityForecast:
    expected_slippage_bps: Decimal
    confidence: Decimal
    stale: bool
    executable: bool
    reason: str

class LiquidityPredictor:
    def __init__(self,max_update_age_ms=500,max_slippage_bps=Decimal("10"),min_confidence=Decimal("0.7")):
        self.max_update_age_ms=max_update_age_ms; self.max_slippage_bps=Decimal(str(max_slippage_bps)); self.min_confidence=Decimal(str(min_confidence))
    def predict(self,snapshot: LiquiditySnapshot, notional: Decimal) -> LiquidityForecast:
        n=Decimal(str(notional)); depth=max(snapshot.depth_notional,Decimal("1")); impact=(n/depth)*Decimal("10000")
        expected=max(snapshot.spread_bps/Decimal("2"),impact)+max(snapshot.trade_rate,Decimal("0"))*Decimal("0.01")
        freshness=max(Decimal("0"),Decimal("1")-Decimal(snapshot.update_age_ms)/Decimal(max(self.max_update_age_ms,1)))
        confidence=min(Decimal("1"),freshness)
        stale=snapshot.update_age_ms>self.max_update_age_ms
        executable=(not stale and confidence>=self.min_confidence and expected<=self.max_slippage_bps)
        reason="ready" if executable else ("stale_market_data" if stale else "liquidity_risk")
        return LiquidityForecast(expected,confidence,stale,executable,reason)
