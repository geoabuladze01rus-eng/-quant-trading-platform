from decimal import Decimal
from market.normalized_orderbook import OrderBookNormalizer

def test_orderbook_is_normalized_and_sorted():
    book = OrderBookNormalizer.normalize('BINANCE', 'BTCUSDT', 123, [('99','2'),('101','1'),('-1','5')], [('103','1'),('102','3'),('0','2')], 7)
    assert book.best_bid.price == Decimal('101')
    assert book.best_bid.quantity == Decimal('1')
    assert book.best_ask.price == Decimal('102')
    assert book.best_ask.quantity == Decimal('3')
    assert book.sequence == 7
