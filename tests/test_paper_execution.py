from decimal import Decimal
from execution.paper_execution import PaperExecutionEngine, PaperPortfolio

def test_round_trip_accounts_for_fees():
    portfolio = PaperPortfolio(Decimal("10000"))
    engine = PaperExecutionEngine(portfolio, Decimal("10"))
    engine.fill("binance", "BTCUSDT", "BUY", Decimal("1"), Decimal("100"), 1000)
    engine.fill("bybit", "BTCUSDT", "SELL", Decimal("1"), Decimal("101"), 1001)
    assert portfolio.base_position == Decimal("0")
    assert portfolio.fees_paid == Decimal("0.201")
    assert portfolio.mark_to_market(Decimal("101")) == Decimal("10000.799")
