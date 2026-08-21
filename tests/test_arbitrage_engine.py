from decimal import Decimal
from strategy.arbitrage_engine import SpotArbitrageEngine, VenueQuote

def test_profitable_net_arbitrage_is_detected():
    engine = SpotArbitrageEngine(min_net_edge_bps=Decimal('10'), fee_bps=Decimal('2'), slippage_bps=Decimal('1'), latency_bps=Decimal('1'))
    quotes = [VenueQuote('BINANCE', Decimal('99'), Decimal('100'), Decimal('5'), Decimal('5')), VenueQuote('BYBIT', Decimal('101'), Decimal('102'), Decimal('5'), Decimal('5'))]
    opportunities = engine.find(quotes)
    assert opportunities[0].buy_venue == 'BINANCE'
    assert opportunities[0].sell_venue == 'BYBIT'
    assert opportunities[0].executable

def test_unhealthy_venue_is_excluded():
    engine = SpotArbitrageEngine(min_net_edge_bps=Decimal('1'))
    quotes = [VenueQuote('BINANCE', Decimal('99'), Decimal('100'), Decimal('5'), Decimal('5'), Decimal('0')), VenueQuote('OKX', Decimal('101'), Decimal('102'), Decimal('5'), Decimal('5'))]
    assert engine.find(quotes) == []
