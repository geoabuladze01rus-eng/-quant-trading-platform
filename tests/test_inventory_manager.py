from decimal import Decimal
from portfolio.inventory_manager import InventoryManager

def test_reservation_reduces_available_balance():
    m = InventoryManager()
    m.set_balance('BINANCE', 'USDT', Decimal('10000'))
    r = m.reserve('BINANCE', 'USDT', Decimal('2500'))
    assert m.available('BINANCE', 'USDT') == Decimal('7500')
    m.release(r)
    assert m.available('BINANCE', 'USDT') == Decimal('10000')

def test_max_arbitrage_quantity_is_limited_by_both_legs():
    m = InventoryManager()
    m.set_balance('BINANCE', 'USDT', Decimal('1000'))
    m.set_balance('BYBIT', 'BTC', Decimal('0.008'))
    qty = m.max_arbitrage_quantity('BINANCE', 'USDT', Decimal('100000'), 'BYBIT', 'BTC', Decimal('1'))
    assert qty == Decimal('0.008')
