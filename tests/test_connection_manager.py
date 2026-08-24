from market.connection_manager import ConnectionManager, ConnectionState


def test_stale_detection_and_reconnect():
    m = ConnectionManager(stale_after_ms=1000)
    m.connecting(); m.connected(1000)
    assert not m.check_stale(1500)
    assert m.check_stale(2501)
    assert m.health.state == ConnectionState.STALE
    m.reconnecting()
    assert m.health.reconnect_count == 1

def test_sequence_gap_is_detected():
    m = ConnectionManager(); m.connected(100)
    m.sequence(10); m.sequence(13)
    assert m.health.dropped_messages == 2
    assert m.health.state == ConnectionState.STALE

def test_heartbeat_recovers_connection_state():
    m = ConnectionManager(); m.connected(100); m.reconnecting(); m.heartbeat(200)
    assert m.health.state == ConnectionState.CONNECTED
