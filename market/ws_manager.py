"""Resilient WebSocket session state machine: heartbeat, reconnect backoff and resync gating."""
from dataclasses import dataclass
from enum import Enum
class ConnectionState(str,Enum): DISCONNECTED="DISCONNECTED"; CONNECTING="CONNECTING"; LIVE="LIVE"; BACKOFF="BACKOFF"; RESYNC="RESYNC"
@dataclass(frozen=True)
class ConnectionHealth:
    state:ConnectionState; reconnect_attempt:int; next_retry_ms:int; last_message_ms:int; resync_required:bool
class WebSocketManager:
    def __init__(self,heartbeat_timeout_ms=3000,base_backoff_ms=250,max_backoff_ms=10000): self.heartbeat_timeout_ms=heartbeat_timeout_ms; self.base_backoff_ms=base_backoff_ms; self.max_backoff_ms=max_backoff_ms; self.state=ConnectionState.DISCONNECTED; self.attempt=0; self.last_message_ms=0; self.next_retry_ms=0; self.resync_required=False
    def connected(self,now_ms): self.state=ConnectionState.LIVE; self.attempt=0; self.last_message_ms=now_ms; self.next_retry_ms=0; self.resync_required=False
    def message(self,now_ms): self.last_message_ms=now_ms
    def sequence_gap(self,now_ms): self.state=ConnectionState.RESYNC; self.resync_required=True; self.last_message_ms=now_ms
    def disconnect(self,now_ms): self.attempt+=1; delay=min(self.max_backoff_ms,self.base_backoff_ms*(2**(self.attempt-1))); self.next_retry_ms=now_ms+delay; self.state=ConnectionState.BACKOFF
    def tick(self,now_ms):
        if self.state==ConnectionState.LIVE and now_ms-self.last_message_ms>self.heartbeat_timeout_ms:self.disconnect(now_ms)
        return ConnectionHealth(self.state,self.attempt,self.next_retry_ms,self.last_message_ms,self.resync_required)
    def resynced(self,now_ms): self.state=ConnectionState.LIVE; self.resync_required=False; self.last_message_ms=now_ms
