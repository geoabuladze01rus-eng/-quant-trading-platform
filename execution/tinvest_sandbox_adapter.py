"""Execution adapter that exposes T-Invest Sandbox through the common router."""

from decimal import Decimal

from connectors.tinvest.sandbox import TInvestSandbox
from execution.router import OrderRequest


class TInvestSandboxExecutionAdapter:
    def __init__(self, sandbox: TInvestSandbox) -> None:
        self._sandbox = sandbox

    async def submit(self, request: OrderRequest) -> object:
        if request.venue != "tinvest-sandbox":
            raise ValueError("T-Invest sandbox adapter received another venue")
        if request.limit_price is None:
            raise ValueError("sandbox adapter requires a limit price")
        return self._sandbox.place_order(
            figi=request.symbol,
            quantity=Decimal(request.quantity),
            price=Decimal(request.limit_price),
            side=request.side,
            idempotency_key=request.client_order_id,
        )
