"""Two-leg paper arbitrage execution with residual tracking."""
from dataclasses import dataclass
from decimal import Decimal

from exchanges.base import Side
from market_data.order_book_aggregator import Book, OrderBookAggregator


@dataclass(frozen=True)
class LegFill:
    venue:str; side:Side; requested:Decimal; filled:Decimal; average_price:Decimal; fee:Decimal; liquid:bool
@dataclass(frozen=True)
class ArbitrageResult:
    buy:LegFill; sell:LegFill; hedging_required:bool; residual:Decimal; status:str
class PaperArbitrageExecutor:
    def __init__(self,fee_bps=Decimal(5)): self.fee_bps=Decimal(str(fee_bps))
    def execute(self,buy_book:Book,sell_book:Book,quantity:Decimal)->ArbitrageResult:
        q=Decimal(str(quantity)); b=OrderBookAggregator.executable(buy_book,"BUY",q); s=OrderBookAggregator.executable(sell_book,"SELL",q)
        bf=Decimal(str(b.notional))*self.fee_bps/Decimal(10000); sf=Decimal(str(s.notional))*self.fee_bps/Decimal(10000)
        buy=LegFill(buy_book.venue,Side.BUY,q,b.quantity,b.average_price,bf,b.sufficient_liquidity)
        sell=LegFill(sell_book.venue,Side.SELL,q,s.quantity,s.average_price,sf,s.sufficient_liquidity)
        residual=abs(b.quantity-s.quantity); hedge=residual>0; status="COMPLETED" if not hedge and b.sufficient_liquidity and s.sufficient_liquidity else ("HEDGE_REQUIRED" if hedge else "REJECTED")
        return ArbitrageResult(buy,sell,hedge,residual,status)
