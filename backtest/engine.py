"""Event-driven historical backtester with explicit costs and portfolio equity."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Callable, Iterable
@dataclass(frozen=True)
class Bar:
    timestamp_ms:int; symbol:str; bid:Decimal; ask:Decimal
@dataclass(frozen=True)
class BacktestTrade:
    timestamp_ms:int; symbol:str; side:str; quantity:Decimal; price:Decimal; fee:Decimal; slippage:Decimal
@dataclass(frozen=True)
class BacktestResult:
    initial_equity:Decimal; final_equity:Decimal; pnl:Decimal; trades:int; total_fees:Decimal; total_slippage:Decimal
class BacktestEngine:
    def __init__(self,initial_cash:Decimal,fee_bps:Decimal=Decimal("5"),slippage_bps:Decimal=Decimal("2")):
        self.initial_cash=Decimal(str(initial_cash)); self.fee_bps=Decimal(str(fee_bps)); self.slippage_bps=Decimal(str(slippage_bps))
    def run(self,bars:Iterable[Bar],signal:Callable[[Bar],str])->BacktestResult:
        cash=self.initial_cash; position=Decimal(0); fees=Decimal(0); slip_total=Decimal(0); trades=0
        for bar in bars:
            action=signal(bar).upper()
            if action not in ("BUY","SELL") or position>0 and action=="BUY" or position<=0 and action=="SELL": continue
            mid=(bar.bid+bar.ask)/Decimal(2); slip=mid*self.slippage_bps/Decimal(10000); price=bar.ask+slip if action=="BUY" else bar.bid-slip; qty=Decimal(1); fee=qty*price*self.fee_bps/Decimal(10000)
            if action=="BUY" and cash>=price+fee: cash-=price+fee; position+=qty
            elif action=="SELL" and position>=qty: cash+=price-fee; position-=qty
            else: continue
            fees+=fee; slip_total+=slip; trades+=1
        final=cash+position*(Decimal("0") if position==0 else mid)
        return BacktestResult(self.initial_cash,final,final-self.initial_cash,trades,fees,slip_total)
