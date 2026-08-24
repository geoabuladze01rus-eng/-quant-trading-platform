"""Priority event bus for low-latency market and macro events."""
import heapq
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any


class EventPriority(IntEnum):
    NORMAL = 10
    IMPORTANT = 50
    HIGH = 90
    CRITICAL = 100

@dataclass(order=True)
class PrioritizedEvent:
    priority: int
    sequence: int
    event_type: str = field(compare=False)
    payload: Any = field(compare=False)
    created_ns: int = field(compare=False, default_factory=time.monotonic_ns)

class EventBus:
    def __init__(self):
        self._queue: list[PrioritizedEvent] = []
        self._sequence = 0

    def publish(self, event_type: str, payload: Any, priority: EventPriority = EventPriority.NORMAL) -> None:
        heapq.heappush(self._queue, PrioritizedEvent(-int(priority), self._sequence, event_type, payload))
        self._sequence += 1

    def next(self) -> PrioritizedEvent | None:
        return heapq.heappop(self._queue) if self._queue else None

    def __len__(self) -> int:
        return len(self._queue)
