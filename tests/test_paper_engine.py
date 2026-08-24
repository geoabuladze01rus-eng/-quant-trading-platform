from decimal import Decimal

from execution.paper_engine import PaperExecutionEngine, PaperOrder


def test_buy_fill_includes_slippage_and_fee():
    e = PaperExecutionEngine()
    e.submit(PaperOrder('o1', 'BINANCE', 'BUY', Decimal(100), Decimal(2), Decimal(10), Decimal(5)))
    f = e.fill('o1', Decimal(1), Decimal(100))
    assert f.filled_price == Decimal('100.05')
    assert f.fee == Decimal('0.10005')

def test_partial_fill_is_supported():
    e = PaperExecutionEngine()
    e.submit(PaperOrder('o1', 'OKX', 'SELL', Decimal(100), Decimal(5)))
    f = e.fill('o1', Decimal(2), Decimal(101))
    assert f.filled_quantity == Decimal(2)
