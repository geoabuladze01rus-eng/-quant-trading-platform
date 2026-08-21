from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from .arbitrage import ArbitrageScanner
from .audit import AuditLog
from .collector_factory import build_public_collector
from .domain import Quote, Venue
from .execution import PaperExecutionEngine
from .pipeline import PaperArbitragePipeline
from .risk import RiskEngine
from .strategies.inter_exchange import InterExchangeArbitrageStrategy


@dataclass(slots=True)
class QuoteCache:
    """Latest normalized quote per venue/symbol for paper-trading decisions."""

    quotes: dict[tuple[Venue, str], Quote] = field(default_factory=dict)

    def update(self, quote: Quote) -> None:
        self.quotes[(quote.venue, quote.symbol)] = quote

    def snapshot(self, symbol: str, venues: tuple[Venue, ...], max_age_ms: int) -> list[Quote]:
        now = datetime.now(timezone.utc)
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
    """Runs public market-data collectors and feeds fresh quotes into paper execution."""

    symbol: str = "BTCUSDT"
    venues: tuple[Venue, ...] = (Venue.BINANCE, Venue.BYBIT, Venue.OKX)
    quantity: Decimal = Decimal("0.001")
    portfolio_value: Decimal = Decimal("100000")
    decision_cooldown_seconds: float = 2.0
    scanner: ArbitrageScanner = field(default_factory=ArbitrageScanner)
    risk: RiskEngine = field(default_factory=RiskEngine)
    execution: PaperExecutionEngine = field(default_factory=PaperExecutionEngine)
    audit: AuditLog = field(default_factory=AuditLog)
    strategy: InterExchangeArbitrageStrategy = field(default_factory=InterExchangeArbitrageStrategy)

    def __post_init__(self) -> None:
        self.cache = QuoteCache()
        self.pipeline = PaperArbitragePipeline(
            scanner=self.scanner,
            risk=self.risk,
            execution=self.execution,
            audit=self.audit,
            strategy=self.strategy,
        )
        self._last_decision_at = 0.0
        self._tasks: list[asyncio.Task[None]] = []

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

    async def start(self) -> None:
        collectors = [build_public_collector(venue, self.symbol, self.on_quote) for venue in self.venues]
        self._tasks = [asyncio.create_task(collector.run()) for collector in collectors]
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


def build_default_runtime() -> RealtimePaperArbitrage:
    return RealtimePaperArbitrage()


if __name__ == "__main__":
    asyncio.run(build_default_runtime().start())
