from decimal import Decimal

from quant_platform.connectors.tinvest import TInvestConnector


def test_tinvest_money_conversion() -> None:
    value = TInvestConnector._money({"units": "123", "nano": 450000000})
    assert value == Decimal("123.45")
