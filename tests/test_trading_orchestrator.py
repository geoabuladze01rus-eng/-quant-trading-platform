"""Integration tests for the risk-gated paper trading pipeline."""
from decimal import Decimal
from strategies.arbitrage_engine import ArbitrageOpportunity
from core.trading_orchestrator import TradingOrchestrator

class Decision:
    def __init__(self, approved, reason): self.approved=approved; self.reason=reason
class Risk:
    def __init__(self, approved=True): self.approved=approved
    def check(self, portfolio_state, notional): return Decision(self.approved, "approved" if self.approved else "risk_rejected")
class Fill:
    def __init__(self, price, fee): self.price=price; self.fee=fee
class Execution:
    def fill(self, venue, symbol, side, quantity, price, timestamp_ms): return Fill(price, Decimal("1"))

def opportunity():
    return ArbitrageOpportunity("BINANCE","BYBIT","BTCUSDT",Decimal("2"),Decimal("100"),Decimal("103"),Decimal("3"),Decimal("4"),Decimal("1"),Decimal("595"),Decimal("0.02975"))

def test_full_pipeline_completes():
    result=TradingOrchestrator(Risk(), object(), Execution()).execute(opportunity(), object(), 100)
    assert result.approved and result.reason == "completed" and result.pnl == Decimal("4")

def test_risk_rejection_stops_execution():
    class NeverExecute:
        def fill(self,*args): raise AssertionError("execution must not be called")
    result=TradingOrchestrator(Risk(False), object(), NeverExecute()).execute(opportunity(), object(), 100)
    assert not result.approved and result.reason == "risk_rejected"
