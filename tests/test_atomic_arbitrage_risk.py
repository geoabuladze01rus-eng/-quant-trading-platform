from decimal import Decimal

import pytest

from quant_platform.domain import OrderIntent, Side, Venue
from quant_platform.execution_group import ArbitrageExecutionGroup
from quant_platform.risk import RiskEngine


def group() -> ArbitrageExecutionGroup:
    buy = OrderIntent(
        Venue.BINANCE,
        "BTCUSDT",
        Side.BUY,
        Decimal(1),
        Decimal(100),
        "test",
        "test",
    )
    sell = OrderIntent(
        Venue.BYBIT,
        "BTCUSDT",
        Side.SELL,
        Decimal(1),
        Decimal(101),
        "test",
        "test",
    )
    return ArbitrageExecutionGroup(buy, sell)


def test_group_requires_equal_cross_venue_legs() -> None:
    execution_group = group()

    assert execution_group.quantity == Decimal(1)
    assert execution_group.expected_gross_edge == Decimal(100)
    assert execution_group.execution_group_id


def test_group_risk_uses_combined_notional() -> None:
    decision = RiskEngine(max_position_pct=Decimal("0.15")).evaluate_group(
        group(),
        Decimal(100000),
    )

    assert decision.approved is False
    assert decision.reason == "arbitrage group size limit exceeded"


def test_group_rejects_non_positive_edge() -> None:
    execution_group = ArbitrageExecutionGroup(
        OrderIntent(
            Venue.BINANCE,
            "BTCUSDT",
            Side.BUY,
            Decimal(1),
            Decimal(101),
            "test",
            "test",
        ),
        OrderIntent(
            Venue.BYBIT,
            "BTCUSDT",
            Side.SELL,
            Decimal(1),
            Decimal(100),
            "test",
            "test",
        ),
    )

    decision = RiskEngine().evaluate_group(execution_group, Decimal(100000))

    assert decision.approved is False
    assert decision.reason == "non-positive gross edge"


def test_group_rejects_same_venue() -> None:
    buy = OrderIntent(
        Venue.BINANCE,
        "BTCUSDT",
        Side.BUY,
        Decimal(1),
        Decimal(100),
        "test",
        "test",
    )
    sell = OrderIntent(
        Venue.BINANCE,
        "BTCUSDT",
        Side.SELL,
        Decimal(1),
        Decimal(101),
        "test",
        "test",
    )

    with pytest.raises(ValueError, match="distinct venues"):
        ArbitrageExecutionGroup(buy, sell)


def test_group_rejects_empty_execution_group_id() -> None:
    execution_group = group()

    with pytest.raises(ValueError, match="execution_group_id must be non-empty"):
        ArbitrageExecutionGroup(
            execution_group.buy,
            execution_group.sell,
            execution_group_id="",
        )
