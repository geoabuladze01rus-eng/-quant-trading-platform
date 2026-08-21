from decimal import Decimal
from risk.portfolio_risk import PortfolioRiskEngine, RiskLimits

def limits():
    return RiskLimits(Decimal('10000'), Decimal('25000'), Decimal('30000'), Decimal('60000'), Decimal('2000'), Decimal('0.10'))

def test_approved_trade():
    r = PortfolioRiskEngine(limits()).evaluate(Decimal('5000'), Decimal('5000'), Decimal('5000'), Decimal('10000'), Decimal('100000'))
    assert r.allowed

def test_daily_loss_triggers_kill_switch():
    e = PortfolioRiskEngine(limits())
    e.update_daily_pnl(Decimal('-2000'))
    r = e.evaluate(Decimal('1'), Decimal('0'), Decimal('0'), Decimal('0'), Decimal('100000'))
    assert not r.allowed and r.reason == 'kill_switch'

def test_drawdown_triggers_kill_switch():
    e = PortfolioRiskEngine(limits())
    e.update_equity(Decimal('100000'))
    r = e.evaluate(Decimal('1'), Decimal('0'), Decimal('0'), Decimal('0'), Decimal('90000'))
    assert not r.allowed and r.reason == 'max_drawdown'
