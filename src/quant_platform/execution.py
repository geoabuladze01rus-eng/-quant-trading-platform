from __future__ import annotations

from dataclasses import dataclass

from .domain import OrderIntent
from .risk import RiskDecision


@dataclass(slots=True)
class PaperExecutionEngine:
    """Safety-first executor. Live exchange calls are intentionally not implemented yet."""

    def submit(self, intent: OrderIntent, risk: RiskDecision) -> dict[str, str]:
        if not risk.approved:
            return {"status": "rejected", "reason": risk.reason}

        return {
            "status": "paper_accepted",
            "venue": intent.venue.value,
            "symbol": intent.symbol,
            "side": intent.side.value,
            "strategy": intent.strategy,
        }
