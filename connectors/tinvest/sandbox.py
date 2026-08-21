"""Isolated T-Invest sandbox adapter.

This module deliberately contains no production-order endpoint and is safe for
paper/integration tests. A real transport can be injected later, but the paper
runtime must depend only on this adapter.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from uuid import uuid4


class SandboxOrderStatus(str, Enum):
    NEW = "NEW"
    CANCELLED = "CANCELLED"
    FILLED = "FILLED"


@dataclass(frozen=True)
class SandboxOrder:
    order_id: str
    idempotency_key: str
    figi: str
    quantity: Decimal
    price: Decimal
    side: str
    status: SandboxOrderStatus = SandboxOrderStatus.NEW


@dataclass
class SandboxAccount:
    account_id: str = field(default_factory=lambda: f"sandbox-{uuid4()}")
    cash: Decimal = Decimal("0")
    orders: dict[str, SandboxOrder] = field(default_factory=dict)
    idempotency: dict[str, str] = field(default_factory=dict)


class TInvestSandbox:
    """Minimal deterministic sandbox used by the paper trading runtime."""

    def __init__(self, account: SandboxAccount | None = None) -> None:
        self.account = account or SandboxAccount()

    def pay_in(self, amount: Decimal) -> Decimal:
        if amount <= 0:
            raise ValueError("sandbox pay-in must be positive")
        self.account.cash += amount
        return self.account.cash

    def place_order(
        self,
        *,
        figi: str,
        quantity: Decimal,
        price: Decimal,
        side: str,
        idempotency_key: str,
    ) -> SandboxOrder:
        if not figi:
            raise ValueError("figi is required")
        if quantity <= 0 or price <= 0:
            raise ValueError("quantity and price must be positive")
        if side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")

        existing_id = self.account.idempotency.get(idempotency_key)
        if existing_id:
            return self.account.orders[existing_id]

        order = SandboxOrder(
            order_id=str(uuid4()),
            idempotency_key=idempotency_key,
            figi=figi,
            quantity=quantity,
            price=price,
            side=side,
        )
        self.account.orders[order.order_id] = order
        self.account.idempotency[idempotency_key] = order.order_id
        return order

    def cancel_order(self, order_id: str) -> SandboxOrder:
        order = self.account.orders[order_id]
        cancelled = SandboxOrder(**{**order.__dict__, "status": SandboxOrderStatus.CANCELLED})
        self.account.orders[order_id] = cancelled
        return cancelled

    def get_order(self, order_id: str) -> SandboxOrder:
        return self.account.orders[order_id]

    def reconcile(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for order in self.account.orders.values():
            counts[order.status.value] = counts.get(order.status.value, 0) + 1
        return counts
