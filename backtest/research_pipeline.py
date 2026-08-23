"""Unified research pipeline for backtest, portfolio, metrics and stress analysis."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Callable, Iterable
from backtest.engine import BacktestEngine, BacktestEvent, BacktestResult
from backtest.portfolio_simulator import PortfolioSimulator, PortfolioBacktestResult
from backtest.stress_engine import StressEngine, StressScenario, StressResult
from risk.metrics_engine import RiskMetricsEngine, RiskMetrics
@dataclass(frozen=True)
class ResearchReport:
    backtest:BacktestResult
    portfolio:PortfolioBacktestResult
    metrics:RiskMetrics
    stress:tuple[StressResult,...]
class ResearchPipeline:
    def __init__(self,backtest=None,portfolio=None,metrics=None,stress=None):
        self.backtest=backtest or BacktestEngine(); self.portfolio=portfolio or PortfolioSimulator(); self.metrics=metrics or RiskMetricsEngine(); self.stress=stress or StressEngine()
    def run(self,events:Iterable[BacktestEvent],scenarios:Iterable[StressScenario]=(),signal:Callable[[BacktestEvent],bool]|None=None,stress_runner:Callable[[StressScenario],Any]|None=None)->ResearchReport:
        bt=self.backtest.run(events,signal); pf=self.portfolio.run(bt.trades)
        equity=pf.initial_equity; returns=[]
        for trade in sorted(bt.trades,key=lambda x:x.timestamp_ms):
            prior=equity; pnl=Decimal(str(trade.net)); equity+=pnl
            returns.append(pnl/prior if prior else Decimal(0))
        rm=self.metrics.calculate(returns)
        sr=self.stress.run(scenarios,stress_runner) if stress_runner else tuple()
        return ResearchReport(bt,pf,rm,sr)
