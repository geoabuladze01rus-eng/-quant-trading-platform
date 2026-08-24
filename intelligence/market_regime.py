"""Deterministic market-regime classifier used as a strategy/risk gate."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class MarketRegime(str, Enum):
    BULL="BULL"; BEAR="BEAR"; SIDEWAYS="SIDEWAYS"; HIGH_VOLATILITY="HIGH_VOLATILITY"; PANIC="PANIC"; LOW_LIQUIDITY="LOW_LIQUIDITY"; UNKNOWN="UNKNOWN"
@dataclass(frozen=True)
class MarketSnapshot:
    price: Decimal; ema_fast: Decimal; ema_slow: Decimal; volatility: Decimal; spread_bps: Decimal; volume_ratio: Decimal; drawdown_pct: Decimal
@dataclass(frozen=True)
class RegimeResult:
    regime: MarketRegime; confidence: Decimal; reasons: tuple[str,...]
class MarketRegimeDetector:
    def __init__(self, high_volatility=Decimal("0.05"), panic_drawdown=Decimal("0.10"), low_volume_ratio=Decimal("0.25"), low_liquidity_spread_bps=Decimal(30)):
        self.high_volatility=high_volatility; self.panic_drawdown=panic_drawdown; self.low_volume_ratio=low_volume_ratio; self.low_liquidity_spread_bps=low_liquidity_spread_bps
    def classify(self,s:MarketSnapshot)->RegimeResult:
        if s.price<=0 or s.ema_fast<=0 or s.ema_slow<=0: return RegimeResult(MarketRegime.UNKNOWN,Decimal(0),("invalid_price_data",))
        if s.spread_bps>=self.low_liquidity_spread_bps or s.volume_ratio<=self.low_volume_ratio: return RegimeResult(MarketRegime.LOW_LIQUIDITY,Decimal("0.95"),("wide_spread_or_low_volume",))
        if s.drawdown_pct>=self.panic_drawdown and s.volatility>=self.high_volatility: return RegimeResult(MarketRegime.PANIC,Decimal("0.98"),("deep_drawdown","high_volatility"))
        if s.volatility>=self.high_volatility: return RegimeResult(MarketRegime.HIGH_VOLATILITY,Decimal("0.90"),("high_volatility",))
        if s.ema_fast>s.ema_slow and s.price>=s.ema_fast: return RegimeResult(MarketRegime.BULL,Decimal("0.85"),("fast_ema_above_slow_ema","price_above_fast_ema"))
        if s.ema_fast<s.ema_slow and s.price<=s.ema_fast: return RegimeResult(MarketRegime.BEAR,Decimal("0.85"),("fast_ema_below_slow_ema","price_below_fast_ema"))
        return RegimeResult(MarketRegime.SIDEWAYS,Decimal("0.70"),("no_directional_confirmation",))
