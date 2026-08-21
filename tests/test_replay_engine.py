from decimal import Decimal
from backtest.replay_engine import MarketEvent, ReplayEngine

def test_replay_is_time_ordered():
    events = [MarketEvent(300, 'OKX', 'BTCUSDT', Decimal('101'), Decimal('102'), Decimal('1'), Decimal('1')), MarketEvent(100, 'BINANCE', 'BTCUSDT', Decimal('99'), Decimal('100'), Decimal('1'), Decimal('1')), MarketEvent(200, 'BYBIT', 'BTCUSDT', Decimal('100'), Decimal('101'), Decimal('1'), Decimal('1'))]
    seen = []
    engine = ReplayEngine(events)
    assert engine.run(lambda e: seen.append(e.timestamp_ms)) == 3
    assert seen == [100, 200, 300]
    assert engine.current_timestamp_ms == 300

def test_reset_clears_runtime_state():
    engine = ReplayEngine([])
    engine.run(lambda _: None)
    engine.reset()
    assert engine.processed == 0
    assert engine.current_timestamp_ms is None
