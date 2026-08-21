"""Spot cross-venue arbitrage opportunity calculator."""
from dataclasses import dataclass
from decimal import Decimal
from market.normalized_orderbook import NormalizedOrderBook

@dataclass(frozen=True)
class ArbitrageOpportunity:
    buy_venue: str
    sell_venue: str
    symbol: str
    quantity: Decimal
    buy_price: Decimal
    sell_price: Decimal
    gross_edge: Decimal
    estimated_fees: Decimal
    estimated_slippage: Decimal
    net_profit: Decimal
    net_return: Decimal

class ArbitrageEngine:
    def __init__(self, min_net_return: Decimal = Decimal('0.001')):
        self.min_net_return = min_net_return

    def find(self, buy, sell, capital, fee_bps, slippage_bps):
        if buy.symbol != sell.symbol or buy.best_ask is None or sell.best_bid is None or capital <= 0: return None
        if buy.best_ask.price >= sell.best_bid.price: return None
        qty = min(buy.best_ask.quantity, sell.best_bid.quantity, capital / buy.best_ask.price)
        if qty <= 0: return None
        buy_price, sell_price = buy.best_ask.price, sell.best_bid.price
        gross = (sell_price - buy_price) * qty
        fees = (buy_price + sell_price) * qty * fee_bps / Decimal('10000')
        slippage = (buy_price + sell_price) * qty * slippage_bps / Decimal('10000')
        net = gross - fees - slippage
        invested = buy_price * qty
        ret = net / invested if invested else Decimal('0')
        if ret < self.min_net_return: return None
        return ArbitrageOpportunity(buy.venue, sell.venue, buy.symbol, qty, buy_price, sell_price, sell_price-buy_price, fees, slippage, net, ret)
