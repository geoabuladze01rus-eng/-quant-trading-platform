"""Async HTTP transport for the T-Invest Sandbox API.

No production URL is accepted. Authentication is supplied at runtime and is
never persisted by this module.
"""

from decimal import Decimal
from typing import Any

import httpx

from .transport import SandboxAccountInfo, SandboxOnlyGuard


class TInvestSandboxHTTP:
    def __init__(self, *, token: str, base_url: str, timeout: float = 10.0) -> None:
        SandboxOnlyGuard(base_url)
        if not token:
            raise ValueError("T-Invest sandbox token is required")
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            headers={"Authorization": f"Bearer {token}"},
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self._client.post(path, json=payload)
        response.raise_for_status()
        return response.json()

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = await self._client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    async def list_accounts(self) -> list[SandboxAccountInfo]:
        data = await self._get("/tinkoff.public.invest.api.contract.v1.SandboxService/GetSandboxAccounts")
        return [
            SandboxAccountInfo(account_id=x["id"], status=x.get("status", "UNKNOWN"))
            for x in data.get("accounts", [])
        ]

    async def pay_in(self, account_id: str, amount: Decimal, currency: str) -> None:
        await self._post(
            "/tinkoff.public.invest.api.contract.v1.SandboxService/SandboxPayIn",
            {"accountId": account_id, "amount": {"units": str(amount), "currency": currency}},
        )

    async def portfolio(self, account_id: str) -> dict[str, Any]:
        return await self._post(
            "/tinkoff.public.invest.api.contract.v1.OperationsService/GetPortfolio",
            {"accountId": account_id},
        )

    async def positions(self, account_id: str) -> dict[str, Any]:
        return await self._post(
            "/tinkoff.public.invest.api.contract.v1.OperationsService/GetPositions",
            {"accountId": account_id},
        )

    async def post_order(self, account_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = dict(payload)
        body["accountId"] = account_id
        return await self._post(
            "/tinkoff.public.invest.api.contract.v1.SandboxService/PostSandboxOrder", body
        )

    async def cancel_order(self, account_id: str, order_id: str) -> dict[str, Any]:
        return await self._post(
            "/tinkoff.public.invest.api.contract.v1.SandboxService/CancelSandboxOrder",
            {"accountId": account_id, "orderId": order_id},
        )

    async def order_state(self, account_id: str, order_id: str) -> dict[str, Any]:
        return await self._post(
            "/tinkoff.public.invest.api.contract.v1.OrdersService/GetOrderState",
            {"accountId": account_id, "orderId": order_id},
        )
