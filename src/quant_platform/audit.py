from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class AuditLog:
    events: list[dict[str, Any]] = field(default_factory=list)

    def record(self, event_type: str, **payload: Any) -> None:
        self.events.append({
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            **payload,
        })

    def last(self) -> dict[str, Any] | None:
        return self.events[-1] if self.events else None
