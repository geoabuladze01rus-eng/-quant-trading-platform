from decimal import Decimal

import pytest

from connectors.tinvest.sandbox import SandboxOrderStatus, TInvestSandbox


def test_sandbox_pay_in_and_idempotent_order():
    sandbox = TInvestSandbox()
    assert sandbox.pay_in(Decimal(100000)) == Decimal(100000)

    first = sandbox.place_order(
        figi="BBG00TESTFIGI",
        quantity=Decimal(1),
        price=Decimal(100),
        side="BUY",
        idempotency_key="strategy-1-leg-1",
    )
    second = sandbox.place_order(
        figi="BBG00TESTFIGI",
        quantity=Decimal(1),
        price=Decimal(100),
        side="BUY",
        idempotency_key="strategy-1-leg-1",
    )

    assert first.order_id == second.order_id
    assert sandbox.reconcile() == {"NEW": 1}


def test_cancel_order_is_reconciled():
    sandbox = TInvestSandbox()
    order = sandbox.place_order(
        figi="BBG00TESTFIGI",
        quantity=Decimal(2),
        price=Decimal(50),
        side="SELL",
        idempotency_key="cancel-me",
    )
    cancelled = sandbox.cancel_order(order.order_id)
    assert cancelled.status is SandboxOrderStatus.CANCELLED
    assert sandbox.get_order(order.order_id).status is SandboxOrderStatus.CANCELLED
    assert sandbox.reconcile() == {"CANCELLED": 1}


@pytest.mark.parametrize(
    "kwargs",
    [
        {"figi": "", "quantity": Decimal(1), "price": Decimal(1), "side": "BUY"},
        {"figi": "X", "quantity": Decimal(0), "price": Decimal(1), "side": "BUY"},
        {"figi": "X", "quantity": Decimal(1), "price": Decimal(0), "side": "BUY"},
        {"figi": "X", "quantity": Decimal(1), "price": Decimal(1), "side": "HOLD"},
    ],
)
def test_invalid_orders_are_rejected(kwargs):
    sandbox = TInvestSandbox()
    with pytest.raises(ValueError):
        sandbox.place_order(**kwargs, idempotency_key="invalid")
