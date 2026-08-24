"""Risk-aware two-leg arbitrage execution planner."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Leg:
    venue:str; side:str; symbol:str; quantity:Decimal; limit_price:Decimal
@dataclass(frozen=True)
class ExecutionPlan:
    buy:Leg; sell:Leg; net_edge_bps:Decimal; max_notional:Decimal; valid:bool; reason:str
class ArbitrageExecutionRouter:
    def plan(self,symbol,buy_venue,sell_venue,buy_ask,sell_bid,quantity,buy_balance,sell_balance,min_edge_bps=Decimal(5),cost_bps=Decimal(4)):
        q=Decimal(str(quantity)); ask=Decimal(str(buy_ask)); bid=Decimal(str(sell_bid)); edge=(bid/ask-1)*Decimal(10000)-Decimal(str(cost_bps)); max_q=min(q,Decimal(str(buy_balance))/ask if ask>0 else Decimal(0),Decimal(str(sell_balance)))
        valid=buy_venue!=sell_venue and ask>0 and bid>0 and max_q>0 and edge>=Decimal(str(min_edge_bps)); reason="ready" if valid else "edge_or_balance_invalid"
        return ExecutionPlan(Leg(buy_venue,"BUY",symbol,max_q,ask),Leg(sell_venue,"SELL",symbol,max_q,bid),edge,max_q*ask,valid,reason)
