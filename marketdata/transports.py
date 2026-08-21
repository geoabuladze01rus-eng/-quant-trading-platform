"""Transport abstractions for live exchange feeds.

The transport owns connection lifecycle; parsing/normalization stays in adapters.
"""
from dataclasses import dataclass
import asyncio
import random
from typing import Awaitable, Callable, Protocol

@dataclass(frozen=True)
class TransportConfig:
    reconnect_base_s: float = 0.5
    reconnect_max_s: float = 30.0
    max_attempts: int = 10

class WebSocketClient(Protocol):
    async def connect(self) -> None: ...
    async def receive(self) -> str: ...
    async def close(self) -> None: ...

class ReconnectingTransport:
    def __init__(self, factory: Callable[[], Awaitable[WebSocketClient]], on_message: Callable[[str], Awaitable[None]], config: TransportConfig | None = None) -> None:
        self.factory = factory
        self.on_message = on_message
        self.config = config or TransportConfig()
        self.running = False
        self.attempt = 0

    async def run(self) -> None:
        self.running = True
        self.attempt = 0
        while self.running:
            client = None
            try:
                client = await self.factory()
                await client.connect()
                self.attempt = 0
                while self.running:
                    await self.on_message(await client.receive())
            except asyncio.CancelledError:
                raise
            except Exception:
                self.attempt += 1
                if self.attempt >= self.config.max_attempts:
                    self.running = False
                    raise
                delay = min(self.config.reconnect_max_s, self.config.reconnect_base_s * (2 ** (self.attempt - 1)))
                delay *= random.uniform(0.8, 1.2)
                await asyncio.sleep(delay)
            finally:
                if client is not None:
                    try:
                        await client.close()
                    except Exception:
                        pass

    def stop(self) -> None:
        self.running = False
