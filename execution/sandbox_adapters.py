"""Testnet/demo adapters: transport-neutral, no production endpoints or keys."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from execution.exchange_adapter import NormalizedOrder, NormalizedOrderResult
@dataclass(frozen=True)
class SandboxConfig:
    venue:str; rest_base_url:str; websocket_url:str; simulated:bool=True
class SandboxAdapter:
    def __init__(self,config:SandboxConfig,transport:Any): self.config=config; self.venue=config.venue; self.transport=transport
    async def submit(self,order:NormalizedOrder)->NormalizedOrderResult: return await self.transport.submit(self.config,order)
    async def cancel(self,exchange_order_id:str)->bool: return await self.transport.cancel(self.config,exchange_order_id)
    async def order_status(self,exchange_order_id:str)->NormalizedOrderResult: return await self.transport.status(self.config,exchange_order_id)
BINANCE_TESTNET=SandboxConfig("binance","https://testnet.binance.vision","wss://stream.testnet.binance.vision/ws",True)
BYBIT_TESTNET=SandboxConfig("bybit","https://api-testnet.bybit.com","wss://stream-testnet.bybit.com/v5/public/spot",True)
OKX_DEMO=SandboxConfig("okx","https://openapi.okx.com","wss://wspap.okx.com:8443/ws/v5/public",True)
