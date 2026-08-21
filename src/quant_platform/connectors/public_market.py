from __future__ import annotations

from decimal import Decimal

import httpx

from ..domain import Quote, Venue
from .base import VenueConnector


class BinanceSpotConnector(VenueConnector):
    venue = Venue.BINANCE

    def __init__(self, base_url: str = "https://data-api.binance.vision") -> None:
        self.base_url = base_url.rstrip("/")

    async def get_quote(self, symbol: str) -> Quote:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(
                f"{self.base_url}/api/v3/ticker/bookTicker",
                params={"symbol": symbol},
            )
            response.raise_for_status()
            data = response.json()
        return Quote.now(
            self.venue,
            symbol,
            data["bidPrice"],
            data["askPrice"],
            data["bidQty"],
            data["askQty"],
        )

    async def get_balance(self, asset: str) -> Decimal:
        raise RuntimeError("public Binance market-data endpoint cannot provide private balances")


class BybitSpotConnector(VenueConnector):
    venue = Venue.BYBIT

    def __init__(self, base_url: str = "https://api.bybit.com") -> None:
        self.base_url = base_url.rstrip("/")

    async def get_quote(self, symbol: str) -> Quote:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(
                f"{self.base_url}/v5/market/tickers",
                params={"category": "spot", "symbol": symbol},
            )
            response.raise_for_status()
            data = response.json()["result"]["list"][0]
        return Quote.now(
            self.venue,
            symbol,
            data["bid1Price"],
            data["ask1Price"],
            data["bid1Size"],
            data["ask1Size"],
        )

    async def get_balance(self, asset: str) -> Decimal:
        raise RuntimeError("public Bybit market-data endpoint cannot provide private balances")


class OKXSpotConnector(VenueConnector):
    venue = Venue.OKX

    def __init__(self, base_url: str = "https://www.okx.com") -> None:
        self.base_url = base_url.rstrip("/")

    async def get_quote(self, symbol: str) -> Quote:
        inst_id = symbol.replace("USDT", "-USDT") if "-" not in symbol else symbol
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(
                f"{self.base_url}/api/v5/market/ticker",
                params={"instId": inst_id},
            )
            response.raise_for_status()
            data = response.json()["data"][0]
        return Quote.now(
            self.venue,
            symbol,
            data["bidPx"],
            data["askPx"],
            data["bidSz"],
            data["askSz"],
        )

    async def get_balance(self, asset: str) -> Decimal:
        raise RuntimeError("public OKX market-data endpoint cannot provide private balances")
