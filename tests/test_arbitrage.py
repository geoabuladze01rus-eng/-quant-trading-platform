from datetime import datetime, timezone
from decimal import Decimal

from quant_platform.arbitrage import ArbitrageScanner
from quant_platform.domain import Quote, Venue


def q(venue: Venue, bid: str, ask: str) -> Quote:
    return Quote(
        venue=venue,
        symbol="BTCUSDT",
        bid=Decimal(bid),
        ask=Decimal(ask),
        bid_size=Decimal("1"),
        ask_size=Decimal("1"),
        timestamp=datetime.now(timezone.utc),
    )


def test_scanner_finds_net_profitable_spread() -> None:
    scanner = ArbitrageScanner(min_net_edge_bps=Decimal("5"))
    opportunity = scanner.scan(
        [q(Venue.BINANCE, "100000", "100001"), q(Venue.BYBIT, "100150", "100151")],
        Decimal("0.01"),
    )

    assert opportunity is not None
    assert opportunity.buy_venue == Venue.BINANCE
    assert opportunity.sell_venue == Venue.BYBIT
    assert opportunity.net_edge_bps > Decimal("5")


def test_scanner_ignores_unprofitable_spread() -> None:
    scanner = ArbitrageScanner(min_net_edge_bps=Decimal("5"))
    opportunity = scanner.scan(
        [q(Venue.BINANCE, "100000", "100010"), q(Venue.BYBIT, "100010", "100020")],
        Decimal("0.01"),
    )

    assert opportunity is None
