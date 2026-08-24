from decimal import Decimal

from execution.liquidity_simulator import LiquiditySimulator, LiquiditySnapshot


def test_partial_fill_is_limited_by_available_liquidity():
    book = LiquiditySnapshot(Decimal(100), Decimal(101), Decimal("0.4"), Decimal("0.5"), 1000)
    result = LiquiditySimulator().execute(book, "BUY", Decimal(1))
    assert result.quantity == Decimal("0.5")
    assert not result.filled
    assert result.reason == "partial_fill"

def test_full_fill_when_liquidity_is_sufficient():
    book = LiquiditySnapshot(Decimal(100), Decimal(101), Decimal(2), Decimal(2), 1000)
    result = LiquiditySimulator().execute(book, "SELL", Decimal(1))
    assert result.quantity == Decimal(1)
    assert result.filled
