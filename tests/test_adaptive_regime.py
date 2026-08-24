from decimal import Decimal

from strategies.adaptive_regime import (
    AdaptiveProfileSelector,
    MarketRegime,
    MarketSnapshot,
    RegimeClassifier,
)


def s(v,liq,tr,sp): return MarketSnapshot(Decimal(str(v)),Decimal(str(liq)),Decimal(str(tr)),Decimal(str(sp)))
def test_regimes():
    c=RegimeClassifier()
    assert c.classify(s(.02,.8,0,5))==MarketRegime.NORMAL
    assert c.classify(s(.02,.8,.8,5))==MarketRegime.TRENDING
    assert c.classify(s(.05,.8,0,5))==MarketRegime.HIGH_VOLATILITY
    assert c.classify(s(.02,.1,0,5))==MarketRegime.LOW_LIQUIDITY
    assert c.classify(s(.10,.8,0,5))==MarketRegime.STRESS

def test_risky_profiles_disable_strategy():
    p=AdaptiveProfileSelector()
    assert not p.select(MarketRegime.LOW_LIQUIDITY).enabled
    assert not p.select(MarketRegime.STRESS).enabled
