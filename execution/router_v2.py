"""Exchange-agnostic execution router with idempotency and partial-fill state."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class OrderState(str,Enum): NEW="NEW"; SUBMITTED="SUBMITTED"; PARTIAL="PARTIAL"; FILLED="FILLED"; CANCEL_PENDING="CANCEL_PENDING"; CANCELED="CANCELED"; FAILED="FAILED"
@dataclass(frozen=True)
class OrderRequest: client_order_id:str; venue:str; symbol:str; side:str; quantity:Decimal; limit_price:Decimal|None=None
@dataclass(frozen=True)
class OrderStatus: client_order_id:str; state:OrderState; filled_qty:Decimal; avg_price:Decimal
class ExecutionRouter:
    def __init__(self): self.orders={}
    def submit(self,request:OrderRequest)->OrderStatus:
        if request.client_order_id in self.orders:return self.orders[request.client_order_id]
        if request.quantity<=0: raise ValueError("quantity must be positive")
        status=OrderStatus(request.client_order_id,OrderState.SUBMITTED,Decimal(0),Decimal(0)); self.orders[request.client_order_id]=status; return status
    def update_fill(self,client_order_id,filled_qty,avg_price,complete=False):
        old=self.orders[client_order_id]; qty=Decimal(str(filled_qty)); state=OrderState.FILLED if complete else (OrderState.PARTIAL if qty>0 else old.state); status=OrderStatus(client_order_id,state,qty,Decimal(str(avg_price))); self.orders[client_order_id]=status; return status
    def mark_cancel_pending(self,client_order_id):
        old=self.orders[client_order_id]; status=OrderStatus(client_order_id,OrderState.CANCEL_PENDING,old.filled_qty,old.avg_price); self.orders[client_order_id]=status; return status
