from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import httpx

from ..domain import OrderIntent, Quote, Side, Venue
from .base import VenueConnector


class TInvestConnector(VenueConnector):
    """T-Invest connector with a sandbox-first account/order surface.

    The connector never exposes the user's token to clients and never enables
    production order submission in the research build.
    """

    venue = Venue.TINVEST

    def __init__(
        self,
        token: str,
        sandbox: bool = True,
        base_url: str | None = None,
    ) -> None:
        if not token:
            raise ValueError("T-Invest API token is required")
        self.token = token
        self.sandbox = sandbox
        self.base_url = (base_url or (
            "https://sandbox-invest-public-api.tbank.ru/rest"
            if sandbox else "https://invest-public-api.tbank.ru/rest"
        )).rstrip("/")

    @staticmethod
    def _money(value: dict[str, object]) -> Decimal:
        units = Decimal(str(value.get("units", "0")))
        nano = Decimal(str(value.get("nano", "0"))) / Decimal("1000000000")
        return units + nano

    async def _post(self, service_method: str, payload: dict[str, object]) -> dict:
        url = f"{self.base_url}/{service_method}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def get_accounts(self) -> dict:
        method = (
            "tinkoff.public.invest.api.contract.v1.SandboxService/GetSandboxAccounts"
            if self.sandbox else
            "tinkoff.public.invest.api.contract.v1.UsersService/GetAccounts"
        )
        return await self._post(method, {})

    async def open_sandbox_account(self, name: str = "quant-platform") -> str:
        if not self.sandbox:
            raise RuntimeError("sandbox account creation is only available in sandbox mode")
        data = await self._post(
            "tinkoff.public.invest.api.contract.v1.SandboxService/OpenSandboxAccount",
            {"name": name},
        )
        return str(data["accountId"])

    async def sandbox_pay_in(self, account_id: str, rub_amount: Decimal) -> dict:
        if not self.sandbox:
            raise RuntimeError("sandbox_pay_in is only available in sandbox mode")
        if rub_amount <= 0:
            raise ValueError("rub_amount must be positive")
        units = int(rub_amount)
        nano = int((rub_amount - units) * Decimal("1000000000"))
        return await self._post(
            "tinkoff.public.invest.api.contract.v1.SandboxService/SandboxPayIn",
            {"accountId": account_id, "amount": {"currency": "rub", "units": str(units), "nano": nano}},
        )

    async def get_portfolio(self, account_id: str) -> dict:
        service = "SandboxService/GetSandboxPortfolio" if self.sandbox else "OperationsService/GetPortfolio"
        return await self._post(
            f"tinkoff.public.invest.api.contract.v1.{service}",
            {"accountId": account_id},
        )

    async def get_positions(self, account_id: str) -> dict:
        service = "SandboxService/GetSandboxPositions" if self.sandbox else "OperationsService/GetPositions"
        return await self._post(
            f"tinkoff.public.invest.api.contract.v1.{service}",
            {"accountId": account_id},
        )

    async def get_last_price(self, instrument_id: str) -> Decimal:
        data = await self._post(
            "tinkoff.public.invest.api.contract.v1.MarketDataService/GetLastPrices",
            {"instrumentId": [instrument_id]},
        )
        prices = data.get("lastPrices", [])
        if not prices:
            raise LookupError(f"no T-Invest price for {instrument_id}")
        return self._money(prices[0]["price"])

    async def get_quote(self, symbol: str) -> Quote:
        raise NotImplementedError(
            "Use the instrument registry plus GetOrderBook for normalized T-Invest quotes"
        )

    async def get_balance(self, asset: str) -> Decimal:
        raise NotImplementedError("Use get_portfolio(account_id) until account context is added")

    async def submit_sandbox_order(
        self,
        account_id: str,
        instrument_id: str,
        quantity_lots: int,
        side: Side,
        order_type: str = "ORDER_TYPE_MARKET",
        price: dict[str, object] | None = None,
    ) -> dict:
        if not self.sandbox:
            raise RuntimeError("sandbox order method requires sandbox mode")
        if quantity_lots <= 0:
            raise ValueError("quantity_lots must be positive")
        direction = "ORDER_DIRECTION_BUY" if side is Side.BUY else "ORDER_DIRECTION_SELL"
        payload: dict[str, object] = {
            "quantity": str(quantity_lots),
            "direction": direction,
            "accountId": account_id,
            "orderType": order_type,
            "orderId": str(uuid4()),
            "instrumentId": instrument_id,
        }
        if price is not None:
            payload["price"] = price
        return await self._post(
            "tinkoff.public.invest.api.contract.v1.SandboxService/PostSandboxOrder",
            payload,
        )

    async def cancel_sandbox_order(self, account_id: str, order_id: str) -> dict:
        if not self.sandbox:
            raise RuntimeError("sandbox cancellation requires sandbox mode")
        return await self._post(
            "tinkoff.public.invest.api.contract.v1.SandboxService/CancelSandboxOrder",
            {"accountId": account_id, "orderId": order_id},
        )

    async def submit_live(self, intent: OrderIntent) -> str:
        raise RuntimeError("live T-Invest execution is disabled in the research build")

    async def cancel_live(self, order_id: str) -> None:
        raise RuntimeError("live T-Invest execution is disabled in the research build")
