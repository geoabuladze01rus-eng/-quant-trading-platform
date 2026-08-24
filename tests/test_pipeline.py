from datetime import UTC, datetime
from decimal import Decimal

from quant_platform.arbitrage import ArbitrageScanner
from quant_platform.audit import AuditLog
from quant_platform.domain import Quote, Venue
from quant_platform.execution import PaperExecutionEngine
from quant_platform.execution_orchestrator import ExecutionState
from quant_platform.pipeline import PaperArbitragePipeline
from quant_platform.risk import RiskEngine
from quant_platform.strategies.inter_exchange import InterExchangeArbitrageStrategy


def test_paper_pipeline_accepts_both_legs_as_one_execution_group() -> None:
    now = datetime.now(UTC)
    quotes = [
        Quote(
            Venue.BINANCE,
            "BTCUSDT",
            Decimal(100000),
            Decimal(100001),
            Decimal(1),
            Decimal(1),
            now,
        ),
        Quote(
            Venue.BYBIT,
            "BTCUSDT",
            Decimal(100250),
            Decimal(100251),
            Decimal(1),
            Decimal(1),
            now,
        ),
    ]
    audit = AuditLog()
    execution = PaperExecutionEngine()
    pipeline = PaperArbitragePipeline(
        scanner=ArbitrageScanner(min_net_edge_bps=Decimal(5)),
        risk=RiskEngine(max_position_pct=Decimal(5)),
        execution=execution,
        audit=audit,
        strategy=InterExchangeArbitrageStrategy(),
    )

    result = pipeline.run(quotes, Decimal(100000), Decimal("0.01"))

    assert result["status"] == "paper_accepted"
    assert len(result["results"]) == 2
    execution_group_id = result["execution_group_id"]
    assert execution_group_id
    assert {
        leg["execution_group_id"] for leg in result["results"]
    } == {execution_group_id}
    assert len({leg["correlation_id"] for leg in result["results"]}) == 2
    for leg in result["results"]:
        assert (
            execution.orchestrator.current_state(leg["execution_id"])
            is ExecutionState.SUBMITTED
        )

    assert audit.last() is not None
    assert audit.last()["event_type"] == "paper_trade_accepted"
    assert audit.last()["execution_group_id"] == execution_group_id
