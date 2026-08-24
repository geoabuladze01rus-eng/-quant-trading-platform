from decimal import Decimal

from intelligence.macro_news_guard import MacroEvent, MacroNewsGuard, NewsImpact


def test_extreme_event_halts_entries():
    event = MacroEvent("fed", "fomc-1", "FOMC decision", 100000, NewsImpact.EXTREME, Decimal(1))
    state = MacroNewsGuard().evaluate(event, 100000)
    assert state.halt_new_entries
    assert state.risk_multiplier == Decimal(0)

def test_high_impact_event_reduces_risk():
    event = MacroEvent("macro", "cpi-1", "CPI", 100000, NewsImpact.HIGH)
    state = MacroNewsGuard().evaluate(event, 100020)
    assert state.halt_new_entries
    assert state.risk_multiplier == Decimal("0.25")

def test_medium_event_reduces_but_does_not_halt():
    event = MacroEvent("macro", "ppi-1", "PPI", 100000, NewsImpact.MEDIUM)
    state = MacroNewsGuard().evaluate(event, 100050)
    assert not state.halt_new_entries
    assert state.risk_multiplier == Decimal("0.50")
