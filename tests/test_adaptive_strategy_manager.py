from decimal import Decimal
from intelligence.adaptive_strategy_manager import AdaptiveStrategyManager, StrategyStats, StrategyState

def stats(name, trades=500, sharpe='1.5', dd='0.05', pf='1.5', exp='0.10'):
    return StrategyStats(name, trades, Decimal(sharpe), Decimal(dd), Decimal(pf), Decimal(exp))

def test_unproven_strategy_gets_small_risk():
    d = AdaptiveStrategyManager().evaluate(stats('new', trades=50))
    assert d.state == StrategyState.CHALLENGER
    assert d.risk_multiplier == Decimal('0.25')

def test_degraded_strategy_goes_to_quarantine():
    d = AdaptiveStrategyManager().evaluate(stats('bad', dd='0.20'))
    assert d.state == StrategyState.QUARANTINE
    assert d.risk_multiplier == Decimal('0')

def test_better_challenger_enters_canary():
    d = AdaptiveStrategyManager().evaluate(stats('champ', sharpe='1.5', exp='0.10'), stats('chall', sharpe='1.8', exp='0.15'))
    assert d.strategy == 'chall'
    assert d.state == StrategyState.CHALLENGER
    assert d.risk_multiplier == Decimal('0.05')
