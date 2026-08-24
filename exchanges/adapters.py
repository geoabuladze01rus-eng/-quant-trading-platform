"""Concrete venue adapters: transport-independent skeletons for Binance, Bybit and OKX."""
from exchanges.base import ExchangeAdapter
from exchanges.resilience import ExchangeResilience


class HttpTransport:
    async def request(self,*args,**kwargs): raise NotImplementedError("bind authenticated venue transport")
class BaseAdapter(ExchangeAdapter):
    def __init__(self,transport=None,resilience=None): self.transport=transport or HttpTransport(); self.resilience=resilience or ExchangeResilience()
    async def place_order(self,request): raise NotImplementedError
    async def cancel_order(self,order_id): raise NotImplementedError
    async def get_order(self,order_id): raise NotImplementedError
    async def get_balance(self,asset): raise NotImplementedError
    async def health(self):
        try:return bool(await self.transport.request("health"))
        except Exception:  # noqa: BLE001 - health checks fail closed on transport errors
            return False
class BinanceAdapter(BaseAdapter):
    @property
    def venue(self):return "binance"
class BybitAdapter(BaseAdapter):
    @property
    def venue(self):return "bybit"
class OKXAdapter(BaseAdapter):
    @property
    def venue(self):return "okx"
