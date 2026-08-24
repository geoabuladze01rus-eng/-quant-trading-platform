"""Async WebSocket feed abstraction with reconnect/backoff and normalized callbacks."""
import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FeedEvent:
    venue:str; channel:str; symbol:str; payload:Any; received_at_ms:int
class WebSocketFeed:
    def __init__(self,venue:str,connect:Callable[[],Awaitable[Any]],handle:Callable[[FeedEvent],Awaitable[None]],backoff_initial:float=0.5,backoff_max:float=15.0): self.venue=venue; self.connect=connect; self.handle=handle; self.backoff_initial=backoff_initial; self.backoff_max=backoff_max; self.running=False
    async def run(self):
        delay=self.backoff_initial; self.running=True
        while self.running:
            try:
                ws=await self.connect(); delay=self.backoff_initial
                async for message in ws: await self.handle(message)
            except asyncio.CancelledError: raise
            except Exception:  # noqa: BLE001 - reconnect on transport failures
                if not self.running: break
                await asyncio.sleep(delay); delay=min(self.backoff_max,delay*2)
    def stop(self): self.running=False
