"""Transport contracts for T-Invest Sandbox.

The production trading runtime must never receive this transport directly.
Only the sandbox adapter may call the sandbox base URL.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class SandboxAccountInfo:
    account_id: str
    status: str


class TInvestSandboxTransport(Protocol):
    async def list_accounts(self) -> list[SandboxAccountInfo]: ...

    async def pay_in(self, account_id: str, amount: Decimal, currency: str) -> None: ...

    async def portfolio(self, account_id: str) -> dict: ...

    async def positions(self, account_id: str) -> dict: ...

    async def post_order(self, account_id: str, payload: dict) -> dict: ...

    async def cancel_order(self, account_id: str, order_id: str) -> dict: ...

    async def order_state(self, account_id: str, order_id: str) -> dict: ...


class SandboxOnlyGuard:
    """Fails closed unless the configured endpoint is explicitly sandbox."""

    def __init__(self, base_url: str) -> None:
        normalized = base_url.rstrip("/").lower()
        if "sandbox" not in normalized:
            raise ValueError("T-Invest paper runtime requires a sandbox endpoint")
        self.base_url = normalized
