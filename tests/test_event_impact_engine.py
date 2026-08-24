from decimal import Decimal

from intelligence.event_impact_engine import EventImpactEngine, ImpactDirection


def test_event_reduces_risk_by_confidence_and_severity():
    impact = EventImpactEngine().evaluate('CPI', 'BTC', ImpactDirection.NEGATIVE, Decimal('0.8'), Decimal('0.5'))
    assert impact.risk_multiplier == Decimal('0.60')

def test_impact_is_bounded():
    impact = EventImpactEngine().evaluate('shock', 'BTC', ImpactDirection.NEGATIVE, Decimal(9), Decimal(9))
    assert impact.risk_multiplier == Decimal(0)
