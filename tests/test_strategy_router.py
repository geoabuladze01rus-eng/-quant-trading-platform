from decimal import Decimal

from intelligence.market_regime import MarketRegime
from intelligence.strategy_router import StrategyRouter

R=StrategyRouter()
def test_panic_blocks_trading():
    p=R.route(MarketRegime.PANIC); assert not p.allowed and p.risk_multiplier==Decimal(0)
def test_low_liquidity_blocks_trading():
    assert not R.route(MarketRegime.LOW_LIQUIDITY).allowed
def test_high_volatility_reduces_size():
    p=R.route(MarketRegime.HIGH_VOLATILITY); assert p.allowed and p.risk_multiplier==Decimal("0.50")
def test_sideways_selects_mean_reversion():
    assert R.route(MarketRegime.SIDEWAYS).strategy=="MEAN_REVERSION_ARBITRAGE"
