"""Deterministic paper execution engine with balances, fees and depth-aware fills."""
from dataclasses import dataclass
from decimal import Decimal

from exchanges.base import Side
from market_data.order_book_aggregator import Book, OrderBookAggregator


@dataclass
class PaperAccount:
    venue:str; quote_balance:Decimal; base_balance:Decimal=Decimal(0)
@dataclass(frozen=True)
class PaperFill:
    venue:str; symbol:str; side:Side; quantity:Decimal; average_price:Decimal; fee:Decimal; sufficient_liquidity:bool
class PaperExecutionEngine:
    def __init__(self,fee_bps=Decimal(10)): self.fee_bps=Decimal(str(fee_bps)); self.accounts={}
    def add_account(self,account:PaperAccount): self.accounts[account.venue]=account
    def execute(self,book:Book,side:Side,quantity:Decimal)->PaperFill:
        q=OrderBookAggregator.executable(book,side.value,Decimal(str(quantity)))
        fee=q.notional*self.fee_bps/Decimal(10000); account=self.accounts[book.venue]
        if q.sufficient_liquidity:
            if side==Side.BUY: account.quote_balance-=q.notional+fee; account.base_balance+=q.quantity
            else: account.base_balance-=q.quantity; account.quote_balance+=q.notional-fee
        return PaperFill(book.venue,book.symbol,side,q.quantity,q.average_price,fee,q.sufficient_liquidity)
