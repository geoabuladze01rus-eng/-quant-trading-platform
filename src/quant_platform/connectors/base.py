from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from ..domain import OrderIntent, Quote, Venue


class VenueConnector(ABC):
    """Common contract. Live order methods stay disabled until paper validation passes."""

    venue: Venue

    @abstractmethod
    async def get_quote(self, symbol: str) -> Quote:
        raise NotImplementedError

    @abstractmethod
    async def get_balance(self, asset: str) -> Decimal:
        raise NotImplementedError

    async def submit_live(self, intent: OrderIntent) -> str:
        raise RuntimeError("live execution is disabled in the research build")

    async def cancel_live(self, order_id: str) -> None:
        raise RuntimeError("live execution is disabled in the research build")
