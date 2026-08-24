from core.event_bus import EventBus, EventPriority


def test_critical_event_precedes_normal():
    bus = EventBus()
    bus.publish('ticker', {}, EventPriority.NORMAL)
    bus.publish('exchange_outage', {}, EventPriority.CRITICAL)
    assert bus.next().event_type == 'exchange_outage'

def test_same_priority_preserves_order():
    bus = EventBus()
    bus.publish('a', {}, EventPriority.HIGH)
    bus.publish('b', {}, EventPriority.HIGH)
    assert bus.next().event_type == 'a'
    assert bus.next().event_type == 'b'
