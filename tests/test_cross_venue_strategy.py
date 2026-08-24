from dataclasses import dataclass
from decimal import Decimal

from arbitrage.cross_venue_strategy import CrossVenueArbitrageStrategy, StrategyConfig
from arbitrage.opportunity_scanner import Opportunity


@dataclass
class Q:
    approved: bool; score: Decimal; reason: str
class Quality:
    def evaluate(self,*args): return Q(True,Decimal(80),"approved")
class Persistence:
    def observe(self,*args):
        return type("S",(),{"confirmations":3})()
class Sizer:
    def size(self,*args): return type("Z",(),{"allowed":Decimal(1),"notional":Decimal(100)})()
class Risk:
    def evaluate(self,**kwargs): return type("R",(),{"allow_trade":True,"reason":"approved"})()
class Scanner:
    def scan(self,*args):
        return [Opportunity("BTC/USDT","BINANCE","BYBIT",Decimal(1),Decimal(100),Decimal(101),Decimal(80))]

def test_strategy_produces_risk_gated_intent():
    x=CrossVenueArbitrageStrategy(Scanner(),Quality(),Persistence(),Sizer(),Risk())
    cfg=StrategyConfig(Decimal(20),1000,Decimal(100),2,Decimal("0.9"),Decimal(1),Decimal(5))
    exposure=lambda opp,n: type("E",(),{"ok":True,"drawdown_state":"NORMAL"})()
    intents=x.evaluate([],{},Decimal(100000),cfg,10,Decimal(10),Decimal("0.1"),Decimal(0),{},[],exposure)
    assert intents[0].approved and intents[0].quantity==Decimal(1)
    assert x.best_approved(intents) is intents[0]
