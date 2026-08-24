"""Provider-agnostic WebSocket lifecycle state machine."""
from dataclasses import dataclass
from enum import Enum


class ConnectionState(str, Enum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    DEGRADED = "DEGRADED"
    RECONNECTING = "RECONNECTING"

@dataclass
class ConnectionHealth:
    venue: str
    state: ConnectionState = ConnectionState.DISCONNECTED
    reconnect_attempts: int = 0
    last_message_ms: int | None = None
    sequence_gaps: int = 0

class WebSocketLifecycle:
    def __init__(self, venue: str, stale_after_ms: int = 5000):
        self.health = ConnectionHealth(venue)
        self.stale_after_ms = stale_after_ms

    def connecting(self): self.health.state = ConnectionState.CONNECTING
    def connected(self, now_ms: int):
        self.health.state = ConnectionState.CONNECTED
        self.health.last_message_ms = now_ms
        self.health.reconnect_attempts = 0
    def message(self, now_ms: int):
        self.health.last_message_ms = now_ms
        if self.health.state in {ConnectionState.DEGRADED, ConnectionState.RECONNECTING}:
            self.health.state = ConnectionState.CONNECTED
    def sequence_gap(self):
        self.health.sequence_gaps += 1
        self.health.state = ConnectionState.DEGRADED
    def check_stale(self, now_ms: int) -> bool:
        if self.health.last_message_ms is None: return True
        stale = now_ms - self.health.last_message_ms > self.stale_after_ms
        if stale:
            self.health.state = ConnectionState.RECONNECTING
            self.health.reconnect_attempts += 1
        return stale
