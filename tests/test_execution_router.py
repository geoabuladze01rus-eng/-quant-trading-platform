from decimal import Decimal

import pytest

from execution.router import ExecutionRouter, OrderRequest


class Gate:
    def __init__(self, allowed: bool) -> None:
        self.allowed = allowed

    def approve(self, request: OrderRequest) -> bool:
        return self.allowed


class Connector:
    def __init__(self) -> None:
        self.received = None

    async def submit(self, request: OrderRequest) -> str:
        self.received = request
        return "paper-order"


@pytest.mark.asyncio
async def test_router_requires_risk_approval() -> None:
    connector = Connector()
    router = ExecutionRouter(Gate(False), {"tinvest-sandbox": connector})
    request = OrderRequest("tinvest-sandbox", "FIGI", "BUY", Decimal(1), Decimal(100), "id-1")
    with pytest.raises(PermissionError):
        await router.submit(request)
    assert connector.received is None


@pytest.mark.asyncio
async def test_router_dispatches_after_approval() -> None:
    connector = Connector()
    router = ExecutionRouter(Gate(True), {"tinvest-sandbox": connector})
    request = OrderRequest("tinvest-sandbox", "FIGI", "BUY", Decimal(1), Decimal(100), "id-1")
    result = await router.submit(request)
    assert result == "paper-order"
    assert connector.received == request
