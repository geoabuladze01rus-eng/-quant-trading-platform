"""Deterministic paper exchange for safe integration tests; never touches a real venue."""
from decimal import Decimal

from .models import NormalizedBalance, NormalizedOrder, OrderSide, OrderStatus


class MockExchangeAdapter:
    venue="MOCK"
    def __init__(self, balances=None, fee_rate=Decimal("0.001"), slippage_bps=Decimal(0)):
        self._balances=balances or {}; self.fee_rate=Decimal(str(fee_rate)); self.slippage_bps=Decimal(str(slippage_bps)); self.orders={}; self._seq=0; self.connected=True
    def health(self): return self.connected
    def balances(self): return [NormalizedBalance(self.venue,a,Decimal(str(v)),Decimal(0)) for a,v in self._balances.items()]
    def positions(self): return []
    def fees(self,symbol): return self.fee_rate
    def place_order(self,symbol,side,quantity,price=None):
        if not self.connected: raise RuntimeError("mock exchange disconnected")
        q=Decimal(str(quantity)); p=Decimal(str(price)) if price is not None else None; self._seq+=1; oid=f"MOCK-{self._seq}"
        if p is None: status=OrderStatus.NEW; filled=Decimal(0)
        else:
            d=Decimal(1)+self.slippage_bps/Decimal(10000); fill=p*d if side==OrderSide.BUY else p/d; base,quote=symbol.split("/"); cost=q*fill; fee=cost*self.fee_rate
            if side==OrderSide.BUY:
                if self._balances.get(quote,Decimal(0))<cost+fee: raise RuntimeError("insufficient quote balance")
                self._balances[quote]-=cost+fee; self._balances[base]=self._balances.get(base,Decimal(0))+q
            else:
                if self._balances.get(base,Decimal(0))<q: raise RuntimeError("insufficient base balance")
                self._balances[base]-=q; self._balances[quote]=self._balances.get(quote,Decimal(0))+cost-fee
            status=OrderStatus.FILLED; filled=q
        o=NormalizedOrder(self.venue,oid,oid,symbol,side,q,filled,p,status,Decimal(0),"",0); self.orders[oid]=o; return o
    def cancel_order(self,order_id):
        o=self.orders.get(order_id)
        if not o or o.status==OrderStatus.FILLED:return False
        self.orders[order_id]=NormalizedOrder(o.venue,o.order_id,o.client_order_id,o.symbol,o.side,o.quantity,o.filled_quantity,o.price,OrderStatus.CANCELED,o.fee,o.fee_asset,o.timestamp_ms); return True
    def get_order(self,order_id): return self.orders[order_id]
