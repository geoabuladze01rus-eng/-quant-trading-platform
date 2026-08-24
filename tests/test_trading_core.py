from decimal import Decimal

from core.trading_core import TradingCore
from intelligence.market_regime import MarketRegime
from risk.risk_engine import PortfolioState


def test_core_blocks_panic():
    p = PortfolioState(Decimal(100000), Decimal(100000))
    d = TradingCore().decide(MarketRegime.PANIC, "BTCUSDT", "binance", Decimal(500), p)
    assert not d.approved
    assert d.intent is None

def test_core_applies_strategy_risk_multiplier():
    p = PortfolioState(Decimal(100000), Decimal(100000))
    d = TradingCore().decide(MarketRegime.BEAR, "BTCUSDT", "binance", Decimal(500), p)
    assert d.approved
    assert d.intent.notional == Decimal(250)
    assert d.intent.strategy == "DEFENSIVE_ARBITRAGE"
