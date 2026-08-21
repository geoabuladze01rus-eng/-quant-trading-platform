from decimal import Decimal
from strategies.inter_exchange_arbitrage import ArbitrageSignal, Quote
from backtesting.arbitrage_simulator import ArbitrageSimulator

def test_simulator_caps_quantity_by_available_liquidity() -> None:
    buy = Quote("binance", "BTCUSDT", Decimal("100"), Decimal("100"), Decimal("1"), Decimal("0.2"), 1000)
    sell = Quote("bybit", "BTCUSDT", Decimal("101"), Decimal("101"), Decimal("0.1"), Decimal("1"), 1000)
    signal = ArbitrageSignal("binance", "bybit", "BTCUSDT", Decimal("1"), Decimal("0.01"), Decimal("0.003"), Decimal("0.007"))
    fill = ArbitrageSimulator({"binance": Decimal("0.001"), "bybit": Decimal("0.001")}, Decimal("2")).execute(signal, buy, sell)
    assert fill is not None
    assert fill.quantity == Decimal("0.1")
    assert fill.net_pnl > 0

def test_simulator_rejects_empty_liquidity() -> None:
    buy = Quote("binance", "BTCUSDT", Decimal("100"), Decimal("100"), Decimal("0"), Decimal("0"), 1000)
    sell = Quote("bybit", "BTCUSDT", Decimal("101"), Decimal("101"), Decimal("0"), Decimal("0"), 1000)
    signal = ArbitrageSignal("binance", "bybit", "BTCUSDT", Decimal("1"), Decimal("0.01"), Decimal("0"), Decimal("0.01"))
    assert ArbitrageSimulator({}).execute(signal, buy, sell) is None
