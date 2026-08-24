from decimal import Decimal

from quant_platform.domain import OrderIntent, Side, Venue
from quant_platform.risk import RiskEngine


def test_risk_rejects_when_daily_loss_limit_is_reached() -> None:
    engine = RiskEngine(daily_pnl_pct=Decimal("-2.0"))
    intent = OrderIntent(
        venue=Venue.BINANCE,
        symbol="BTCUSDT",
        side=Side.BUY,
        quantity=Decimal("0.01"),
        limit_price=Decimal(100000),
        strategy="test",
        reason="unit test",
    )

    decision = engine.evaluate(intent, Decimal(100000))

    assert decision.approved is False
    assert decision.reason == "daily loss limit reached"


def test_risk_approves_small_paper_order() -> None:
    engine = RiskEngine()
    intent = OrderIntent(
        venue=Venue.BYBIT,
        symbol="BTCUSDT",
        side=Side.BUY,
        quantity=Decimal("0.001"),
        limit_price=Decimal(100000),
        strategy="test",
        reason="unit test",
    )

    decision = engine.evaluate(intent, Decimal(100000))

    assert decision.approved is True
