from decimal import Decimal

from core.adaptive_control_loop import AdaptiveControlLoop, MacroRisk
from intelligence.adaptive_strategy_manager import StrategyStats


def s(name='champ', sharpe='1.5', dd='0.05', exp='0.10'):
    return StrategyStats(name, 500, Decimal(sharpe), Decimal(dd), Decimal('1.5'), Decimal(exp))

def test_macro_risk_multiplies_strategy_risk():
    d = AdaptiveControlLoop().evaluate(s(), MacroRisk('HIGH', Decimal('0.5'), 'macro event'))
    assert d.allowed
    assert d.final_risk_multiplier == Decimal('0.5')

def test_zero_macro_multiplier_blocks_trade():
    d = AdaptiveControlLoop().evaluate(s(), MacroRisk('EXTREME', Decimal(0), 'extreme event'))
    assert not d.allowed
    assert d.final_risk_multiplier == Decimal(0)
