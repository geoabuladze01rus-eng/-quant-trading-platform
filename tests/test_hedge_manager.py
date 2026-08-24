from execution.hedge_manager import HedgeManager


def test_balanced_legs_need_no_hedge():
    d=HedgeManager().assess(2,2,2,5)
    assert d.action=="NONE" and d.residual_quantity==0

def test_partial_sell_requires_sell_hedge():
    d=HedgeManager().assess(2,1,2,5)
    assert d.action=="SELL_HEDGE" and d.residual_quantity==1

def test_excessive_hedge_slippage_kills():
    d=HedgeManager().assess(2,1,2,50)
    assert d.action=="KILL"
