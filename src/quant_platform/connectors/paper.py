from __future__ import annotations

from decimal import Decimal

from ..domain import Quote, Venue
from .base import VenueConnector


class PaperVenueConnector(VenueConnector):
    """Deterministic connector used for integration tests and paper simulations."""

    def __init__(self, venue: Venue, quotes: dict[str, Quote], balances: dict[str, Decimal] | None = None) -> None:
        self.venue = venue
        self._quotes = quotes
        self._balances = balances or {}

    async def get_quote(self, symbol: str) -> Quote:
        quote = self._quotes.get(symbol)
        if quote is None:
            raise KeyError(f"no paper quote for {self.venue.value}:{symbol}")
        return quote

    async def get_balance(self, asset: str) -> Decimal:
        return self._balances.get(asset, Decimal(0))
