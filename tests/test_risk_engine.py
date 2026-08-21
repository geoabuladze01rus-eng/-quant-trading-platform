from decimal import Decimal
from risk.risk_engine import PortfolioState, RiskEngine

def test_daily_loss_kills_new_trade():
    state = PortfolioState(Decimal("98000"), Decimal("100000"))
    decision = RiskEngine().check(state, Decimal("500"))
    assert not decision.approved
    assert decision.reason == "daily_loss_limit"

def test_trade_size_is_limited():
    state = PortfolioState(Decimal("100000"), Decimal("100000"))
    decision = RiskEngine().check(state, Decimal("1001"))
    assert not decision.approved
    assert decision.reason == "trade_notional_limit"

def test_kill_switch_has_priority():
    state = PortfolioState(Decimal("100000"), Decimal("100000"), kill_switch=True)
    assert not RiskEngine().check(state, Decimal("100")).approved

def test_valid_trade_is_approved():
    state = PortfolioState(Decimal("100000"), Decimal("100000"))
    assert RiskEngine().check(state, Decimal("500")).approved
