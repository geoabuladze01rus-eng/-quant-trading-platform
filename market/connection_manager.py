"""Exchange-agnostic WebSocket connection lifecycle state."""
from dataclasses import dataclass
from enum import Enum

class ConnectionState(str, Enum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    STALE = "STALE"
    RECONNECTING = "RECONNECTING"

@dataclass
class ConnectionHealth:
    state: ConnectionState = ConnectionState.DISCONNECTED
    last_message_ms: int | None = None
    last_sequence: int | None = None
    reconnect_count: int = 0
    dropped_messages: int = 0

class ConnectionManager:
    def __init__(self, stale_after_ms: int = 5000):
        if stale_after_ms <= 0: raise ValueError("stale_after_ms must be positive")
        self.stale_after_ms = stale_after_ms
        self.health = ConnectionHealth()
    def connecting(self): self.health.state = ConnectionState.CONNECTING
    def connected(self, timestamp_ms: int):
        self.health.state = ConnectionState.CONNECTED
        self.health.last_message_ms = timestamp_ms
    def heartbeat(self, timestamp_ms: int):
        self.health.last_message_ms = timestamp_ms
        if self.health.state in {ConnectionState.STALE, ConnectionState.RECONNECTING}: self.health.state = ConnectionState.CONNECTED
    def sequence(self, sequence: int):
        if self.health.last_sequence is not None and sequence > self.health.last_sequence + 1:
            self.health.dropped_messages += sequence - self.health.last_sequence - 1
            self.health.state = ConnectionState.STALE
        self.health.last_sequence = sequence
    def check_stale(self, now_ms: int) -> bool:
        last = self.health.last_message_ms
        stale = last is None or now_ms - last > self.stale_after_ms
        if stale: self.health.state = ConnectionState.STALE
        return stale
    def reconnecting(self):
        self.health.state = ConnectionState.RECONNECTING
        self.health.reconnect_count += 1
