from decimal import Decimal

from core.event_bus import EventPriority
from intelligence.event_impact_engine import ImpactDirection
from market.event_router import MarketEventRouter


def test_critical_external_event_updates_risk():
    router = MarketEventRouter()
    router.publish_external('FOMC', 'BTC', Decimal(1), Decimal(1), ImpactDirection.NEGATIVE, 'shock')
    event = router.process_next()
    assert event.event_type == 'external_impact'
    assert event.priority == -int(EventPriority.CRITICAL)
    assert router.state.risk_multiplier == Decimal(0)

def test_market_price_updates_state():
    router = MarketEventRouter()
    router.publish_market('ticker', 'BTCUSDT', {'price': '100000'})
    router.process_next()
    assert router.state.prices['BTCUSDT'] == Decimal(100000)
