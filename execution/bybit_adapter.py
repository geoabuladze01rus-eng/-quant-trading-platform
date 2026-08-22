"""Bybit adapter: converts normalized orders to a thin injected-client interface."""
from execution.exchange_adapter import NormalizedOrder,NormalizedOrderResult
from decimal import Decimal
class BybitAdapter:
    venue="bybit"
    def __init__(self,client): self.client=client
    async def submit(self,order:NormalizedOrder)->NormalizedOrderResult:
        p={"category":"spot","symbol":order.symbol,"side":order.side.value,"orderType":order.order_type.value,"qty":str(order.quantity),"orderLinkId":order.client_order_id}
        if order.price is not None:p.update({"price":str(order.price),"timeInForce":"GTC"})
        raw=await self.client.place_order(**p); r=raw.get("result",raw); oid=str(r.get("orderId") or r.get("orderLinkId")); return NormalizedOrderResult(oid,"NEW",Decimal(0),None)
    async def cancel(self,exchange_order_id:str)->bool: await self.client.cancel_order(category="spot",orderId=exchange_order_id); return True
    async def order_status(self,exchange_order_id:str)->NormalizedOrderResult:
        r=await self.client.get_order(category="spot",orderId=exchange_order_id); r=r.get("result",r); return NormalizedOrderResult(str(exchange_order_id),str(r.get("orderStatus","UNKNOWN")),Decimal(str(r.get("cumExecQty",0))),Decimal(str(r["avgPrice"])) if r.get("avgPrice") else None)
