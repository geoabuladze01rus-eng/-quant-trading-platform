"""Exchange WebSocket payload parsers for normalized top-of-book feeds."""
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from marketdata.adapters import RawBookTicker


@dataclass(frozen=True)
class WebSocketConfig:
    url: str
    symbol: str

class BookTickerParser:
    @staticmethod
    def binance(payload: dict[str, Any]) -> RawBookTicker:
        return RawBookTicker(payload["s"], Decimal(payload["b"]), Decimal(payload["a"]), Decimal(payload["B"]), Decimal(payload["A"]), int(payload["E"]))
    @staticmethod
    def bybit(payload: dict[str, Any]) -> RawBookTicker:
        data = payload["data"]
        return RawBookTicker(data["s"], Decimal(data["b"]), Decimal(data["a"]), Decimal(data["B"]), Decimal(data["A"]), int(payload.get("ts", 0)))
    @staticmethod
    def okx(payload: dict[str, Any]) -> RawBookTicker:
        data = payload["data"][0]
        return RawBookTicker(data["instId"], Decimal(data["bidPx"]), Decimal(data["askPx"]), Decimal(data["bidSz"]), Decimal(data["askSz"]), int(payload.get("ts", 0)))

class PaperWebSocketFeed:
    """Parses exchange payloads for paper tests; never sends orders."""
    def __init__(self, parser: Callable[[dict[str, Any]], RawBookTicker]) -> None:
        self.parser = parser
    def parse(self, payload: dict[str, Any]) -> RawBookTicker:
        return self.parser(payload)
