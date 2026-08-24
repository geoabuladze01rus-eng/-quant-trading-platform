from market.ws_connection import ConnectionState, WebSocketLifecycle


def test_stale_connection_enters_reconnecting():
    c = WebSocketLifecycle('BINANCE', stale_after_ms=1000)
    c.connected(1000)
    assert c.check_stale(2501)
    assert c.health.state == ConnectionState.RECONNECTING
    assert c.health.reconnect_attempts == 1

def test_sequence_gap_degrades_connection():
    c = WebSocketLifecycle('OKX')
    c.connected(100)
    c.sequence_gap()
    assert c.health.state == ConnectionState.DEGRADED
    assert c.health.sequence_gaps == 1
