from decimal import Decimal
from execution.realistic_simulator import OrderBookSnapshot, RealisticExecutionSimulator

def test_partial_fill_and_fee():
    book = OrderBookSnapshot(Decimal('100'), Decimal('101'), Decimal('5'), Decimal('2'), 1000)
    fill = RealisticExecutionSimulator(fee_bps=Decimal('10'), latency_ms=25).execute('BUY', Decimal('5'), book, 1000)
    assert fill.filled_qty == Decimal('2')
    assert fill.average_price == Decimal('101')
    assert fill.fee == Decimal('0.202')
    assert fill.latency_ms == 25

def test_invalid_side_rejected():
    book = OrderBookSnapshot(Decimal('100'), Decimal('101'), Decimal('5'), Decimal('5'), 1000)
    try:
        RealisticExecutionSimulator().execute('HOLD', Decimal('1'), book, 1000)
        assert False
    except ValueError:
        assert True
