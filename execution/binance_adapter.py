"""Binance adapter skeleton: normalization only; credentials/network are injected."""
from decimal import Decimal

from execution.exchange_adapter import NormalizedOrder, NormalizedOrderResult


class BinanceAdapter:
    venue="binance"
    def __init__(self,client): self.client=client
    async def submit(self,order:NormalizedOrder)->NormalizedOrderResult:
        params={"symbol":order.symbol,"side":order.side.value,"type":order.order_type.value,"quantity":str(order.quantity),"newClientOrderId":order.client_order_id}
        if order.price is not None: params.update({"price":str(order.price),"timeInForce":"GTC"})
        raw=await self.client.create_order(**params)
        fills=raw.get("fills",[]); qty=sum(float(f.get("qty",0)) for f in fills); notional=sum(float(f.get("qty",0))*float(f.get("price",0)) for f in fills)
        avg=notional/qty if qty else None
        return NormalizedOrderResult(str(raw["orderId"]),str(raw.get("status","UNKNOWN")),Decimal(str(qty)),Decimal(str(avg)) if avg is not None else None)
    async def cancel(self,exchange_order_id:str)->bool:
        await self.client.cancel_order(orderId=exchange_order_id); return True
    async def order_status(self,exchange_order_id:str)->NormalizedOrderResult:
        raw=await self.client.get_order(orderId=exchange_order_id)
        return NormalizedOrderResult(str(raw["orderId"]),str(raw.get("status","UNKNOWN")),Decimal(str(raw.get("executedQty",0))),None)
