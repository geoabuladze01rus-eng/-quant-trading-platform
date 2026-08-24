from decimal import Decimal

from execution.fault_injection import ExecutionScenario, FaultInjector


def test_partial_fill_and_slippage():
    f=FaultInjector(ExecutionScenario(fill_ratio=Decimal("0.5"), slippage_bps=Decimal(10)))
    assert f.effective_quantity(Decimal(2)) == Decimal(1)
    assert f.adjusted_price(Decimal(100), "BUY") == Decimal("100.1")
    assert f.adjusted_price(Decimal(100), "SELL") == Decimal("99.9")

def test_second_leg_failure_can_be_simulated():
    f=FaultInjector(ExecutionScenario(fail_sell=True))
    assert not f.should_fail("BUY") and f.should_fail("SELL")
