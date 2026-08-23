from decimal import Decimal
from quant_platform.domain import OrderIntent, Side, Venue
from quant_platform.execution_orchestrator import ExecutionOrchestrator, ExecutionState
from quant_platform.risk import RiskDecision

def intent():
    return OrderIntent(Venue.BINANCE,"BTCUSDT",Side.BUY,Decimal("0.01"),None,"arb","test")

def test_rejected_execution_stops_before_submit():
    execution_id,events=ExecutionOrchestrator().start(intent(),RiskDecision(False,"daily loss"))
    assert execution_id
    assert events[0].state is ExecutionState.RISK_REJECTED

def test_approved_execution_enters_submitted():
    execution_id,events=ExecutionOrchestrator().start(intent(),RiskDecision(True,"ok"))
    assert execution_id
    assert events[0].state is ExecutionState.SUBMITTED

def test_lifecycle_transitions_keep_execution_id():
    oid,_=ExecutionOrchestrator().start(intent(),RiskDecision(True,"ok"))
    event=ExecutionOrchestrator().transition(oid,ExecutionState.PARTIALLY_FILLED,"partial")
    assert event.execution_id==oid
