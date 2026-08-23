from decimal import Decimal
import pytest
from quant_platform.domain import OrderIntent, Side, Venue
from quant_platform.execution_group import ArbitrageExecutionGroup
from quant_platform.risk import RiskEngine

def group():
    buy = OrderIntent(Venue.BINANCE, "BTCUSDT", Side.BUY, Decimal("1"), Decimal("100"), "test", "test")
    sell = OrderIntent(Venue.BYBIT, "BTCUSDT", Side.SELL, Decimal("1"), Decimal("101"), "test", "test")
    return ArbitrageExecutionGroup(buy, sell)

def test_group_requires_equal_cross_venue_legs():
    g = group()
    assert g.quantity == Decimal("1")
    assert g.expected_gross_edge == Decimal("100")

def test_group_risk_uses_combined_notional():
    decision = RiskEngine(max_position_pct=Decimal("0.15")).evaluate_group(group(), Decimal("100000"))
    assert decision.approved is False
    assert decision.reason == "arbitrage group size limit exceeded"

def test_group_rejects_non_positive_edge():
    g = ArbitrageExecutionGroup(
        OrderIntent(Venue.BINANCE, "BTCUSDT", Side.BUY, Decimal("1"), Decimal("101"), "test", "test"),
        OrderIntent(Venue.BYBIT, "BTCUSDT", Side.SELL, Decimal("1"), Decimal("100"), "test", "test"),
    )
    decision = RiskEngine().evaluate_group(g, Decimal("100000"))
    assert decision.approved is False
    assert decision.reason == "non-positive gross edge"

def test_group_rejects_same_venue():
    buy = OrderIntent(Venue.BINANCE, "BTCUSDT", Side.BUY, Decimal("1"), Decimal("100"), "test", "test")
    sell = OrderIntent(Venue.BINANCE, "BTCUSDT", Side.SELL, Decimal("1"), Decimal("101"), "test", "test")
    with pytest.raises(ValueError, match="distinct venues"):
        ArbitrageExecutionGroup(buy, sell)
