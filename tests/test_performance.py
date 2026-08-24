from decimal import Decimal

from analytics.performance import PerformanceAnalyzer


def test_performance_metrics():
    r = PerformanceAnalyzer().analyze([Decimal(100), Decimal(-50), Decimal(100), Decimal(-25)], Decimal(10000))
    assert r.total_pnl == Decimal(125)
    assert r.total_return == Decimal('0.0125')
    assert r.win_rate == Decimal('0.5')
    assert r.profit_factor > Decimal('2.6')
    assert r.max_drawdown > 0
    assert r.trades == 4

def test_empty_series():
    r = PerformanceAnalyzer().analyze([], Decimal(10000))
    assert r.trades == 0
    assert r.total_pnl == Decimal(0)
