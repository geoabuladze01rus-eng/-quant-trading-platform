"""Scan normalized cross-venue books and return executable arbitrage candidates."""
from dataclasses import dataclass
from decimal import Decimal
from itertools import permutations
@dataclass(frozen=True)
class Opportunity:
    symbol:str; buy_venue:str; sell_venue:str; quantity:Decimal; buy_price:Decimal; sell_price:Decimal; net_edge_bps:Decimal
class OpportunityScanner:
    def __init__(self,cost_engine): self.cost_engine=cost_engine
    def scan(self,books,quantity,fees,min_edge_bps):
        out=[]
        for buy_book,sell_book in permutations(books,2):
            if buy_book.symbol!=sell_book.symbol: continue
            buy=self._quote(buy_book,"BUY",quantity); sell=self._quote(sell_book,"SELL",quantity)
            if not buy or not sell or not buy.sufficient_liquidity or not sell.sufficient_liquidity: continue
            cost=self.cost_engine.estimate(buy.average_price,sell.average_price,fees[buy_book.venue],fees[sell_book.venue],buy.average_price,sell.average_price,min_edge_bps)
            if cost.executable: out.append(Opportunity(buy_book.symbol,buy_book.venue,sell_book.venue,buy.quantity,buy.average_price,sell.average_price,cost.net_edge_bps))
        return sorted(out,key=lambda x:x.net_edge_bps,reverse=True)
    @staticmethod
    def _quote(book,side,quantity):
        from market_data.order_book_aggregator import OrderBookAggregator
        return OrderBookAggregator.executable(book,side,Decimal(str(quantity)))
