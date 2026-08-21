"""Two-leg inter-exchange arbitrage simulation with liquidity constraints."""
from dataclasses import dataclass
from decimal import Decimal
from strategies.inter_exchange_arbitrage import Quote, ArbitrageSignal

@dataclass(frozen=True)
class ArbitrageFill:
    signal: ArbitrageSignal
    buy_price: Decimal
    sell_price: Decimal
    quantity: Decimal
    gross_pnl: Decimal
    costs: Decimal
    net_pnl: Decimal

class ArbitrageSimulator:
    def __init__(self, fee_rates: dict[str, Decimal], slippage_bps: Decimal = Decimal("2")) -> None:
        self.fee_rates = fee_rates
        self.slippage_bps = slippage_bps

    def execute(self, signal: ArbitrageSignal, buy: Quote, sell: Quote) -> ArbitrageFill | None:
        quantity = min(signal.quantity, buy.ask_size, sell.bid_size)
        if quantity <= 0:
            return None
        buy_price = buy.ask * (Decimal("1") + self.slippage_bps / Decimal("10000"))
        sell_price = sell.bid * (Decimal("1") - self.slippage_bps / Decimal("10000"))
        gross = (sell_price - buy_price) * quantity
        buy_fee = buy_price * quantity * self.fee_rates.get(buy.venue, Decimal("0"))
        sell_fee = sell_price * quantity * self.fee_rates.get(sell.venue, Decimal("0"))
        costs = buy_fee + sell_fee
        return ArbitrageFill(signal, buy_price, sell_price, quantity, gross, costs, gross - costs)
