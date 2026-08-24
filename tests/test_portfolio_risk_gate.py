from decimal import Decimal

from core.portfolio import Portfolio
from execution.router import OrderRequest
from risk.portfolio_gate import PortfolioRiskGate, PortfolioRiskLimits


def request(notional: str) -> OrderRequest:
    return OrderRequest(
        venue="tinvest-sandbox",
        symbol="FIGI",
        side="BUY",
        quantity=Decimal(notional),
        limit_price=Decimal(1),
        client_order_id="risk-test",
    )


def test_rejects_order_above_per_order_limit() -> None:
    portfolio = Portfolio(Decimal(100000), Decimal(100000))
    gate = PortfolioRiskGate(portfolio)
    assert gate.approve(request("5001")) is False


def test_rejects_after_daily_loss_limit() -> None:
    portfolio = Portfolio(Decimal(100000), Decimal(97000))
    gate = PortfolioRiskGate(portfolio)
    assert gate.approve(request("100")) is False


def test_accepts_small_order_in_normal_state() -> None:
    portfolio = Portfolio(Decimal(100000), Decimal(100000))
    gate = PortfolioRiskGate(portfolio, PortfolioRiskLimits(max_order_notional=Decimal("0.05")))
    assert gate.approve(request("100")) is True
