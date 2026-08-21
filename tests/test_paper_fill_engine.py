from decimal import Decimal

from core.portfolio import Portfolio
from paper.fill_engine import PaperFillEngine


def test_buy_fills_at_best_ask_and_updates_portfolio() -> None:
    portfolio = Portfolio(Decimal("10000"), Decimal("10000"))
    engine = PaperFillEngine(portfolio, Decimal("0.001"))
    fill = engine.try_fill(
        symbol="BTCUSDT", side="BUY", quantity=Decimal("0.1"),
        limit_price=Decimal("101"), bid=Decimal("99"), ask=Decimal("100"),
    )
    assert fill is not None
    assert fill.price == Decimal("100")
    assert portfolio.cash == Decimal("9989.990")
    assert portfolio.positions["BTCUSDT"].quantity == Decimal("0.1")


def test_buy_does_not_fill_above_limit() -> None:
    portfolio = Portfolio(Decimal("10000"), Decimal("10000"))
    engine = PaperFillEngine(portfolio)
    assert engine.try_fill(
        symbol="BTCUSDT", side="BUY", quantity=Decimal("0.1"),
        limit_price=Decimal("99"), bid=Decimal("99"), ask=Decimal("100"),
    ) is None
