from __future__ import annotations

import asyncio
import json
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from decimal import Decimal

from websockets.asyncio.client import ClientConnection, connect

from .domain import Quote, Venue

QuoteHandler = Callable[[Quote], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class CollectorStats:
    messages: int = 0
    reconnects: int = 0
    last_message_monotonic: float | None = None
    last_latency_ms: float | None = None


class WebSocketCollector(ABC):
    """Reconnectable public market-data collector. Never submits orders."""

    def __init__(
        self,
        venue: Venue,
        symbol: str,
        handler: QuoteHandler,
        stale_after_seconds: float = 3.0,
    ) -> None:
        self.venue = venue
        self.symbol = symbol
        self.handler = handler
        self.stale_after_seconds = stale_after_seconds
        self._stop = asyncio.Event()
        self._stats = CollectorStats()

    @property
    def stats(self) -> CollectorStats:
        return self._stats

    @abstractmethod
    def websocket_url(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def parse_message(self, payload: dict) -> Quote | None:
        raise NotImplementedError

    async def run(self) -> None:
        backoff = 1.0
        while not self._stop.is_set():
            try:
                async with connect(
                    self.websocket_url(),
                    ping_interval=20,
                    ping_timeout=10,
                    close_timeout=5,
                    max_queue=2048,
                ) as websocket:
                    backoff = 1.0
                    await self._consume(websocket)
            except asyncio.CancelledError:
                raise
            except Exception:
                self._stats = CollectorStats(
                    self._stats.messages,
                    self._stats.reconnects + 1,
                    self._stats.last_message_monotonic,
                    self._stats.last_latency_ms,
                )
                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=backoff)
                except TimeoutError:
                    pass
                backoff = min(backoff * 2.0, 30.0)

    async def stop(self) -> None:
        self._stop.set()

    async def _consume(self, websocket: ClientConnection) -> None:
        loop = asyncio.get_running_loop()
        async for raw in websocket:
            received = loop.time()
            payload = json.loads(raw)
            quote = self.parse_message(payload)
            if quote is None:
                continue
            # Quote.now() timestamps the normalized event at ingestion time. Exchange
            # event timestamps will be added to the domain model before latency-based
            # execution is enabled. For now this metric is explicitly zero rather than
            # pretending to measure network latency.
            self._stats = CollectorStats(
                self._stats.messages + 1,
                self._stats.reconnects,
                received,
                0.0,
            )
            await self.handler(quote)


class BinanceBookTickerCollector(WebSocketCollector):
    def websocket_url(self) -> str:
        return f"wss://stream.binance.com:9443/ws/{self.symbol.lower()}@bookTicker"

    def parse_message(self, payload: dict) -> Quote | None:
        if not {"b", "a", "B", "A"}.issubset(payload):
            return None
        return Quote.now(
            self.venue,
            self.symbol,
            Decimal(payload["b"]),
            Decimal(payload["a"]),
            Decimal(payload["B"]),
            Decimal(payload["A"]),
        )


class BybitTickerCollector(WebSocketCollector):
    def websocket_url(self) -> str:
        return "wss://stream.bybit.com/v5/public/spot"

    async def run(self) -> None:
        async def loop() -> None:
            async with connect(self.websocket_url(), ping_interval=20, ping_timeout=10) as websocket:
                await websocket.send(json.dumps({"op": "subscribe", "args": [f"tickers.{self.symbol}"]}))
                await self._consume(websocket)

        backoff = 1.0
        while not self._stop.is_set():
            try:
                await loop()
                backoff = 1.0
            except asyncio.CancelledError:
                raise
            except Exception:
                self._stats = CollectorStats(
                    self._stats.messages,
                    self._stats.reconnects + 1,
                    self._stats.last_message_monotonic,
                    self._stats.last_latency_ms,
                )
                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=backoff)
                except TimeoutError:
                    pass
                backoff = min(backoff * 2.0, 30.0)

    def parse_message(self, payload: dict) -> Quote | None:
        data = payload.get("data") or {}
        if payload.get("topic") != f"tickers.{self.symbol}" or not data:
            return None
        bid = data.get("bid1Price")
        ask = data.get("ask1Price")
        if not bid or not ask:
            return None
        return Quote.now(
            self.venue,
            self.symbol,
            Decimal(bid),
            Decimal(ask),
            Decimal(data.get("bid1Size", "0")),
            Decimal(data.get("ask1Size", "0")),
        )


class OKXTickerCollector(WebSocketCollector):
    def websocket_url(self) -> str:
        return "wss://ws.okx.com:8443/ws/v5/public"

    async def run(self) -> None:
        async def loop() -> None:
            async with connect(self.websocket_url(), ping_interval=20, ping_timeout=10) as websocket:
                await websocket.send(json.dumps({"op": "subscribe", "args": [{"channel": "tickers", "instId": self.symbol}]}))
                await self._consume(websocket)

        backoff = 1.0
        while not self._stop.is_set():
            try:
                await loop()
                backoff = 1.0
            except asyncio.CancelledError:
                raise
            except Exception:
                self._stats = CollectorStats(
                    self._stats.messages,
                    self._stats.reconnects + 1,
                    self._stats.last_message_monotonic,
                    self._stats.last_latency_ms,
                )
                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=backoff)
                except TimeoutError:
                    pass
                backoff = min(backoff * 2.0, 30.0)

    def parse_message(self, payload: dict) -> Quote | None:
        data = payload.get("data") or []
        if payload.get("arg", {}).get("channel") != "tickers" or not data:
            return None
        item = data[0]
        if not item.get("bidPx") or not item.get("askPx"):
            return None
        return Quote.now(
            self.venue,
            self.symbol,
            Decimal(item["bidPx"]),
            Decimal(item["askPx"]),
            Decimal(item.get("bidSz", "0")),
            Decimal(item.get("askSz", "0")),
        )
