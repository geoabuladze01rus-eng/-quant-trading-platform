"""Market-data event bus with heartbeat and reconnect state."""
from collections.abc import Callable
from dataclasses import dataclass
from time import monotonic


@dataclass(frozen=True)
class ConnectionState:
    venue: str
    connected: bool
    reconnect_attempt: int
    last_message_monotonic: float
class MarketDataBus[T]:
    def __init__(self, heartbeat_timeout_s: float = 2.0, max_reconnect_attempts: int = 10) -> None:
        self.heartbeat_timeout_s = heartbeat_timeout_s
        self.max_reconnect_attempts = max_reconnect_attempts
        self._handlers: list[Callable[[T], None]] = []
        self._states: dict[str, ConnectionState] = {}
    def subscribe(self, handler: Callable[[T], None]) -> None:
        self._handlers.append(handler)
    def connected(self, venue: str) -> None:
        old = self._states.get(venue)
        attempt = old.reconnect_attempt if old else 0
        self._states[venue] = ConnectionState(venue, True, attempt, monotonic())
    def message(self, venue: str, event: T) -> None:
        state = self._states.get(venue)
        if state is None or not state.connected:
            return
        self._states[venue] = ConnectionState(venue, True, state.reconnect_attempt, monotonic())
        for handler in tuple(self._handlers):
            handler(event)
    def heartbeat_ok(self, venue: str) -> bool:
        state = self._states.get(venue)
        return bool(state and state.connected and monotonic() - state.last_message_monotonic <= self.heartbeat_timeout_s)
    def disconnected(self, venue: str) -> ConnectionState:
        old = self._states.get(venue)
        attempt = min((old.reconnect_attempt + 1) if old else 1, self.max_reconnect_attempts)
        state = ConnectionState(venue, False, attempt, old.last_message_monotonic if old else 0.0)
        self._states[venue] = state
        return state
    def state(self, venue: str) -> ConnectionState | None:
        return self._states.get(venue)
