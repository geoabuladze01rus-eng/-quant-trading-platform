"""OKX adapter: maps normalized orders to an injected OKX client."""
from decimal import Decimal

from execution.exchange_adapter import NormalizedOrder, NormalizedOrderResult


class OKXAdapter:
    venue="okx"
    def __init__(self,client): self.client=client
    async def submit(self,order:NormalizedOrder)->NormalizedOrderResult:
        p={"instId":order.symbol,"tdMode":"cash","side":order.side.value.lower(),"ordType":order.order_type.value.lower(),"sz":str(order.quantity),"clOrdId":order.client_order_id}
        if order.price is not None:p["px"]=str(order.price)
        raw=await self.client.place_order(**p); data=(raw.get("data") or [{}])[0]; return NormalizedOrderResult(str(data.get("ordId",order.client_order_id)),"NEW",Decimal(0),None)
    async def cancel(self,exchange_order_id:str)->bool: await self.client.cancel_order(instId="",ordId=exchange_order_id); return True
    async def order_status(self,exchange_order_id:str)->NormalizedOrderResult:
        raw=await self.client.get_order(instId="",ordId=exchange_order_id); data=(raw.get("data") or [{}])[0]; return NormalizedOrderResult(exchange_order_id,str(data.get("state","UNKNOWN")),Decimal(str(data.get("accFillSz",0))),Decimal(str(data["avgPx"])) if data.get("avgPx") else None)
