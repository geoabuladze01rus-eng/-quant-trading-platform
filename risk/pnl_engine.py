"""Canonical PnL calculation for arbitrage trades."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class PnL:
    gross:Decimal; fees:Decimal; funding:Decimal; slippage:Decimal; realized:Decimal; unrealized:Decimal; net:Decimal
class PnLEngine:
    def calculate(self,buy_price,sell_price,quantity,buy_fee,sell_fee,funding=Decimal(0),slippage=Decimal(0),unrealized=Decimal(0))->PnL:
        q=Decimal(str(quantity)); gross=(Decimal(str(sell_price))-Decimal(str(buy_price)))*q
        fees=Decimal(str(buy_fee))+Decimal(str(sell_fee)); fund=Decimal(str(funding)); slip=Decimal(str(slippage)); unr=Decimal(str(unrealized)); realized=gross-fees-fund-slip
        return PnL(gross,fees,fund,slip,realized,unr,realized+unr)
