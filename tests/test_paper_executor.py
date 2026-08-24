from decimal import Decimal

import pytest

from execution.paper_executor import PaperExecutor, Side


def test_paper_buy_and_sell():
    ex = PaperExecutor(Decimal(1000))
    ex.execute('BTCUSDT', Side.BUY, Decimal('0.005'), Decimal(100000))
    assert ex.portfolio.cash == Decimal(500)
    assert ex.portfolio.positions['BTCUSDT'] == Decimal('0.005')
    ex.execute('BTCUSDT', Side.SELL, Decimal('0.005'), Decimal(101000))
    assert ex.portfolio.cash == Decimal(1005)
    assert ex.portfolio.positions['BTCUSDT'] == Decimal(0)

def test_paper_rejects_insufficient_cash():
    ex = PaperExecutor(Decimal(100))
    with pytest.raises(ValueError):
        ex.execute('BTCUSDT', Side.BUY, Decimal(1), Decimal(1000))
