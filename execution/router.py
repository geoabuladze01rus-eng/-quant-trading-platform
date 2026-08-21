"""Venue-agnostic execution router with mandatory risk gate."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class OrderRequest:
    venue: str
    symbol: str
    side: str
    quantity: Decimal
    limit_price: Decimal | None = None
    client_order_id: str = ""


class RiskGate(Protocol):
    def approve(self, request: OrderRequest) -> bool: ...


class ExecutionConnector(Protocol):
    async def submit(self, request: OrderRequest) -> object: ...


class ExecutionRouter:
    """Routes only approved orders; strategies never call venue connectors directly."""

    def __init__(self, risk_gate: RiskGate, connectors: dict[str, ExecutionConnector]) -> None:
        self._risk_gate = risk_gate
        self._connectors = connectors

    async def submit(self, request: OrderRequest) -> object:
        if not self._risk_gate.approve(request):
            raise PermissionError("order rejected by portfolio risk gate")
        connector = self._connectors.get(request.venue)
        if connector is None:
            raise ValueError(f"unsupported execution venue: {request.venue}")
        return await connector.submit(request)
