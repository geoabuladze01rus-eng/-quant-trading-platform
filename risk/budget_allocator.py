"""Portfolio-level risk budget allocator for concurrent arbitrage opportunities."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class BudgetCandidate:
    id: str
    score: Decimal
    notional: Decimal
    risk_weight: Decimal
    correlation_penalty: Decimal = Decimal(0)


@dataclass(frozen=True)
class Allocation:
    id: str
    notional: Decimal
    fraction_of_budget: Decimal


class RiskBudgetAllocator:
    def allocate(
        self,
        candidates: list[BudgetCandidate],
        total_budget: Decimal,
        max_daily_loss: Decimal,
    ) -> list[Allocation]:
        budget = min(Decimal(str(total_budget)), Decimal(str(max_daily_loss)))
        if budget <= 0:
            return []

        minimum_risk = Decimal("0.000001")
        ranked = sorted(
            candidates,
            key=lambda candidate: Decimal(str(candidate.score))
            / max(
                minimum_risk,
                Decimal(str(candidate.risk_weight))
                + Decimal(str(candidate.correlation_penalty)),
            ),
            reverse=True,
        )
        selected: list[tuple[str, Decimal]] = []
        remaining = budget
        for candidate in ranked:
            if remaining <= 0:
                break
            risk = max(
                minimum_risk,
                Decimal(str(candidate.risk_weight))
                + Decimal(str(candidate.correlation_penalty)),
            )
            capacity = min(Decimal(str(candidate.notional)), remaining / risk)
            if capacity <= 0:
                continue
            selected.append((candidate.id, capacity))
            remaining -= capacity * risk

        total = sum((notional for _, notional in selected), Decimal(0))
        return [
            Allocation(
                candidate_id,
                notional,
                notional / total if total else Decimal(0),
            )
            for candidate_id, notional in selected
        ]
