from decimal import Decimal

from execution.slippage import ExecutionCostModel


def test_buy_and_sell_prices_include_market_impact():
    model = ExecutionCostModel(Decimal(10), Decimal(2), Decimal(1))
    assert model.execution_price(Decimal(100), "BUY") == Decimal("100.03")
    assert model.execution_price(Decimal(100), "SELL") == Decimal("99.97")
    assert model.total_cost_bps() == Decimal(13)

def test_fee_is_calculated_on_execution_price():
    model = ExecutionCostModel(Decimal(10), Decimal(2), Decimal(1))
    assert model.fee(Decimal(1), Decimal("100.03")) == Decimal("0.10003")
