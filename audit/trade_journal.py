"""Append-only trading decision journal for auditability and analytics."""
from dataclasses import dataclass, asdict
from decimal import Decimal
import json

@dataclass(frozen=True)
class TradeEvent:
    timestamp_ms: int
    event: str
    symbol: str
    venue: str
    strategy: str
    regime: str
    status: str
    reason: str = ""
    spread_bps: Decimal = Decimal("0")
    expected_net_bps: Decimal = Decimal("0")
    quantity: Decimal = Decimal("0")
    price: Decimal = Decimal("0")
    fee: Decimal = Decimal("0")
    slippage_bps: Decimal = Decimal("0")
    latency_ms: Decimal = Decimal("0")
    pnl: Decimal = Decimal("0")

class TradeJournal:
    def __init__(self) -> None:
        self.events: list[TradeEvent] = []

    def append(self, event: TradeEvent) -> None:
        self.events.append(event)

    def export_jsonl(self) -> str:
        lines = []
        for event in self.events:
            data = asdict(event)
            for key, value in data.items():
                if isinstance(value, Decimal):
                    data[key] = str(value)
            lines.append(json.dumps(data, ensure_ascii=False, sort_keys=True))
        return "\n".join(lines)

    def rejected(self) -> list[TradeEvent]:
        return [e for e in self.events if e.status == "REJECTED"]

    def completed(self) -> list[TradeEvent]:
        return [e for e in self.events if e.status == "COMPLETED"]
