from marketdata.replay_bus import MarketDataBus


def test_bus_delivers_only_when_connected():
    received = []
    bus = MarketDataBus()
    bus.subscribe(received.append)
    bus.message("binance", "ignored")
    assert received == []
    bus.connected("binance")
    bus.message("binance", "tick")
    assert received == ["tick"]

def test_disconnect_increments_reconnect_attempt():
    bus = MarketDataBus(max_reconnect_attempts=2)
    bus.connected("bybit")
    assert bus.disconnected("bybit").reconnect_attempt == 1
    assert bus.disconnected("bybit").reconnect_attempt == 2
