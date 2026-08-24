from datetime import datetime
from decimal import Decimal

from analytics.trade_journal import TradeEvent, TradeJournal, now_utc, performance_report


def event(pnl: str, fee: str = "1") -> TradeEvent:
    return TradeEvent("ORDER_FILLED", now_utc(), "test", "paper", "BTCUSDT", "BUY", Decimal(1), Decimal(100), Decimal(fee), Decimal(pnl), 5.0)

def test_journal_rejects_naive_timestamp() -> None:
    journal = TradeJournal()
    bad = TradeEvent("ORDER_FILLED", datetime.now(), "x", "paper", "BTCUSDT", "BUY", Decimal(1), Decimal(1))  # noqa: DTZ005 - deliberately naive
    try:
        journal.append(bad)
        assert False
    except ValueError:
        assert True

def test_performance_report() -> None:
    report = performance_report([event("10"), event("-5")], Decimal(1000))
    assert report.trades == 2
    assert report.total_fees == Decimal(2)
    assert report.total_pnl == Decimal(3)
    assert report.win_rate == Decimal("0.5")
    assert report.profit_factor == Decimal(2)
    assert report.average_latency_ms == Decimal("5.0")
    assert report.max_drawdown > 0
