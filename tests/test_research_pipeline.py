from decimal import Decimal
from backtest.engine import BacktestEngine, BacktestEvent
from backtest.portfolio_simulator import PortfolioSimulator
from backtest.research_pipeline import ResearchPipeline

def test_pipeline_produces_consistent_pnl_and_equity():
    events = [
        BacktestEvent(1, Decimal("100"), Decimal("101"), Decimal("10")),
        BacktestEvent(2, Decimal("100"), Decimal("99"), Decimal("10")),
    ]
    pipeline = ResearchPipeline(
        backtest=BacktestEngine(fee_bps=Decimal("0")),
        portfolio=PortfolioSimulator(Decimal("1000")),
    )
    report = pipeline.run(events)
    assert report.backtest.total_trades == 2
    assert report.backtest.net_pnl == Decimal("10")
    assert report.portfolio.final_equity == Decimal("1010")
    assert report.portfolio.net_pnl == report.backtest.net_pnl

def test_pipeline_returns_are_sequential_portfolio_returns():
    events = [
        BacktestEvent(1, Decimal("100"), Decimal("110"), Decimal("10")),
        BacktestEvent(2, Decimal("100"), Decimal("110"), Decimal("10")),
    ]
    pipeline = ResearchPipeline(
        backtest=BacktestEngine(fee_bps=Decimal("0")),
        portfolio=PortfolioSimulator(Decimal("1000")),
    )
    report = pipeline.run(events)
    assert report.metrics.observations == 2
    assert report.metrics.mean > Decimal("0")
