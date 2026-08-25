from __future__ import annotations

import asyncio
import math
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from .arbitrage import ArbitrageScanner
from .audit import AuditLog
from .collector_factory import build_public_collector
from .domain import Quote, Venue
from .execution import PaperExecutionEngine
from .execution_checkpoint import JsonExecutionCheckpointStore
from .execution_timeout import (
    ExecutionTimeoutController,
    TimeoutSweepResult,
)
from .pipeline import PaperArbitragePipeline
from .risk import RiskEngine
from .settings import settings
from .strategies.inter_exchange import InterExchangeArbitrageStrategy


@dataclass(slots=True)
class QuoteCache:
    """Latest normalized quote per venue/symbol for paper-trading decisions."""

    quotes: dict[tuple[Venue, str], Quote] = field(default_factory=dict)

    def update(self, quote: Quote) -> None:
        self.quotes[(quote.venue, quote.symbol)] = quote

    def snapshot(self, symbol: str, venues: tuple[Venue, ...], max_age_ms: int) -> list[Quote]:
        now = datetime.now(UTC)
        result: list[Quote] = []
        for venue in venues:
            quote = self.quotes.get((venue, symbol))
            if quote is None:
                continue
            age_ms = (now - quote.timestamp).total_seconds() * 1000
            if age_ms <= max_age_ms:
                result.append(quote)
        return result


@dataclass(slots=True)
class RealtimePaperArbitrage:
    """Run public market-data collectors and feed fresh quotes into paper execution."""

    symbol: str = "BTCUSDT"
    venues: tuple[Venue, ...] = (Venue.BINANCE, Venue.BYBIT, Venue.OKX)
    quantity: Decimal = Decimal("0.001")
    portfolio_value: Decimal = Decimal(100000)
    decision_cooldown_seconds: float = 2.0
    execution_timeout_seconds: float = 5.0
    timeout_sweep_interval_seconds: float = 1.0
    scanner: ArbitrageScanner = field(default_factory=ArbitrageScanner)
    risk: RiskEngine = field(default_factory=RiskEngine)
    execution: PaperExecutionEngine = field(default_factory=PaperExecutionEngine)
    audit: AuditLog = field(default_factory=AuditLog)
    strategy: InterExchangeArbitrageStrategy = field(default_factory=InterExchangeArbitrageStrategy)
    cache: QuoteCache = field(init=False)
    pipeline: PaperArbitragePipeline = field(init=False)
    timeout_controller: ExecutionTimeoutController = field(init=False)
    _last_decision_at: float = field(init=False, default=0.0)
    _tasks: list[asyncio.Task[None]] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        if (
            not math.isfinite(self.execution_timeout_seconds)
            or self.execution_timeout_seconds <= 0
        ):
            raise ValueError("execution timeout must be finite and positive")
        if (
            not math.isfinite(self.timeout_sweep_interval_seconds)
            or self.timeout_sweep_interval_seconds <= 0
        ):
            raise ValueError("timeout sweep interval must be finite and positive")
        self.cache = QuoteCache()
        self.pipeline = PaperArbitragePipeline(
            scanner=self.scanner,
            risk=self.risk,
            execution=self.execution,
            audit=self.audit,
            strategy=self.strategy,
        )
        self.timeout_controller = ExecutionTimeoutController(
            self.execution,
            timeout=timedelta(seconds=self.execution_timeout_seconds),
        )

    async def on_quote(self, quote: Quote) -> None:
        self.cache.update(quote)
        snapshot = self.cache.snapshot(self.symbol, self.venues, self.scanner.max_quote_age_ms)
        if len(snapshot) < 2:
            return

        now = time.monotonic()
        if now - self._last_decision_at < self.decision_cooldown_seconds:
            return

        self._last_decision_at = now
        self.pipeline.run(snapshot, self.portfolio_value, self.quantity)

    def sweep_execution_timeouts(
        self,
        *,
        now: datetime | None = None,
    ) -> tuple[TimeoutSweepResult, ...]:
        results = self.timeout_controller.sweep(now=now)
        for result in results:
            reconciliation = result.reconciliation
            residual = reconciliation.residual if reconciliation is not None else None
            self.audit.record(
                "execution_group_timeout",
                execution_group_id=result.execution_group_id,
                expired_execution_ids=list(result.expired_execution_ids),
                reconciliation_state=(
                    reconciliation.state.value if reconciliation is not None else None
                ),
                residual_signed_quantity=(
                    str(residual.signed_quantity) if residual is not None else None
                ),
                hedge_required=(
                    reconciliation.hedge_required if reconciliation is not None else False
                ),
                resulting_states=[state.value for state in result.resulting_states],
            )
        return results

    async def _timeout_watchdog(self) -> None:
        while True:
            await asyncio.sleep(self.timeout_sweep_interval_seconds)
            self.sweep_execution_timeouts()

    async def start(self) -> None:
        collectors = [build_public_collector(venue, self.symbol, self.on_quote) for venue in self.venues]
        self._tasks = [asyncio.create_task(collector.run()) for collector in collectors]
        self._tasks.append(asyncio.create_task(self._timeout_watchdog()))
        try:
            await asyncio.gather(*self._tasks)
        finally:
            await self.stop()

    async def stop(self) -> None:
        for task in self._tasks:
            if not task.done():
                task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()


def build_default_runtime(
    *,
    checkpoint_path: Path | None = None,
) -> RealtimePaperArbitrage:
    if not settings.paper_trading:
        raise RuntimeError("realtime runtime requires paper trading; live trading is disabled")

    store = JsonExecutionCheckpointStore(
        checkpoint_path or Path(settings.execution_checkpoint_path)
    )
    execution = (
        PaperExecutionEngine.from_checkpoint_store(store)
        if store.path.exists()
        else PaperExecutionEngine(checkpoint_store=store)
    )
    return RealtimePaperArbitrage(
        execution=execution,
        execution_timeout_seconds=settings.execution_timeout_seconds,
        timeout_sweep_interval_seconds=settings.timeout_sweep_interval_seconds,
    )


def main() -> None:
    """Start the safe-by-default real-time paper-trading runtime."""
    asyncio.run(build_default_runtime().start())


if __name__ == "__main__":
    main()
