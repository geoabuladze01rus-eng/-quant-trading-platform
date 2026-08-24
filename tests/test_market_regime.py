from decimal import Decimal

from intelligence.market_regime import MarketRegime, MarketRegimeDetector, MarketSnapshot

D=MarketRegimeDetector()
def snap(**kw):
    base={"price":Decimal(106),"ema_fast":Decimal(105),"ema_slow":Decimal(100),"volatility":Decimal("0.02"),"spread_bps":Decimal(5),"volume_ratio":Decimal(1),"drawdown_pct":Decimal(0)}; base.update(kw); return MarketSnapshot(**base)
def test_bull(): assert D.classify(snap()).regime==MarketRegime.BULL
def test_bear(): assert D.classify(snap(price=Decimal(95),ema_fast=Decimal(95),ema_slow=Decimal(100))).regime==MarketRegime.BEAR
def test_panic_has_priority(): assert D.classify(snap(volatility=Decimal("0.08"),drawdown_pct=Decimal("0.12"))).regime==MarketRegime.PANIC
def test_low_liquidity_blocks_regime_trading(): assert D.classify(snap(spread_bps=Decimal(35))).regime==MarketRegime.LOW_LIQUIDITY
