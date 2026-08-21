from __future__ import annotations

from decimal import Decimal

import httpx

from ..domain import Quote, Venue
from .base import VenueConnector


class TInvestConnector(VenueConnector):
    """Personal T-Invest API connector.

    Uses the user's own Bearer token. It is intentionally not a data-rebroadcast
    service: credentials and account data stay inside the user's private runtime.
    Live order submission remains disabled until the paper-trading gates pass.
    """

    venue = Venue.TINVEST

    def __init__(self, token: str, base_url: str = "https://invest-public-api.tbank.ru/rest") -> None:
        if not token:
            raise ValueError("T-Invest API token is required")
        self.token = token
        self.base_url = base_url.rstrip("/")

    @staticmethod
    def _money(value: dict[str, object]) -> Decimal:
        units = Decimal(str(value.get("units", "0")))
        nano = Decimal(str(value.get("nano", "0"))) / Decimal("1000000000")
        return units + nano

    async def get_last_price(self, instrument_id: str) -> Decimal:
        url = f"{self.base_url}/tinkoff.public.invest.api.contract.v1.MarketDataService/GetLastPrices"
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {"instrumentId": [instrument_id]}
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        prices = data.get("lastPrices", [])
        if not prices:
            raise LookupError(f"no T-Invest price for {instrument_id}")
        return self._money(prices[0]["price"])

    async def get_quote(self, symbol: str) -> Quote:
        raise NotImplementedError(
            "T-Invest quote normalization requires instrument UID/FIGI mapping and order-book data; "
            "use get_last_price until the instrument registry is implemented"
        )

    async def get_balance(self, asset: str) -> Decimal:
        raise NotImplementedError("T-Invest account service will be wired in the account connector milestone")
