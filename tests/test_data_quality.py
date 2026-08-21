from decimal import Decimal
from market.data_quality import DataQualityMonitor

def test_stale_data_lowers_score():
    q = DataQualityMonitor(stale_after_ms=1000).evaluate(Decimal('100'), Decimal('101'), 0, 2001)
    assert q.stale
    assert q.score < Decimal('1')

def test_sequence_gap_is_not_trusted():
    q = DataQualityMonitor().evaluate(Decimal('100'), Decimal('101'), 1000, 1001, sequence_gap=True)
    assert q.sequence_gap
    assert q.score == Decimal('0.65')

def test_crossed_book_is_invalid():
    q = DataQualityMonitor().evaluate(Decimal('101'), Decimal('100'), 1000, 1000)
    assert q.crossed_book
    assert q.score == Decimal('0.50')
