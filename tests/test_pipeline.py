from datetime import datetime, timezone
from decimal import Decimal

from quant_platform.arbitrage import ArbitrageScanner
from quant_platform.audit import AuditLog
from quant_platform.domain import Quote, Venue
from quant_platform.execution import PaperExecutionEngine
from quant_platform.pipeline import PaperArbitragePipeline
from quant_platform.risk import RiskEngine
from quant_platform.strategies.inter_exchange import InterExchangeArbitrageStrategy


def test_paper_pipeline_accepts_both_legs() -> None:
    now = datetime.now(timezone.utc)
    quotes = [
        Quote(Venue.BINANCE, "BTCUSDT", Decimal("100000"), Decimal("100001"), Decimal("1"), Decimal("1"), now),
        Quote(Venue.BYBIT, "BTCUSDT", Decimal("100150"), Decimal("100151"), Decimal("1"), Decimal("1"), now),
    ]
    audit = AuditLog()
    pipeline = PaperArbitragePipeline(
        scanner=ArbitrageScanner(min_net_edge_bps=Decimal("5")),
        risk=RiskEngine(max_position_pct=Decimal("5")),
        execution=PaperExecutionEngine(),
        audit=audit,
        strategy=InterExchangeArbitrageStrategy(),
    )

    result = pipeline.run(quotes, Decimal("100000"), Decimal("0.01"))

    assert result["status"] == "paper_accepted"
    assert len(result["results"]) == 2
    assert audit.last() is not None
    assert audit.last()["event_type"] == "paper_trade_accepted"
