from decimal import Decimal

from analytics.performance_engine import PerformanceEngine


def test_performance_metrics():
    report = PerformanceEngine().report([Decimal(10), Decimal(-5), Decimal(8)], Decimal(1))
    assert report.trades == 3
    assert report.total_pnl == Decimal(12)
    assert report.gross_profit == Decimal(18)
    assert report.gross_loss == Decimal(5)
    assert report.fees == Decimal(1)
    assert report.max_drawdown == Decimal(5)

def test_empty_report():
    report = PerformanceEngine().report([])
    assert report.trades == 0
    assert report.total_pnl == Decimal(0)
