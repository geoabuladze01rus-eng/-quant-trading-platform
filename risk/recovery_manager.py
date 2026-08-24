"""Controlled recovery after a circuit-breaker trip; never auto-resumes directly to live trading."""
from dataclasses import dataclass
from enum import Enum


class RecoveryState(str, Enum):
    TRIPPED="TRIPPED"; DIAGNOSTIC="DIAGNOSTIC"; SAFE="SAFE"; PAPER="PAPER"; LIVE="LIVE"; FAILED="FAILED"

@dataclass(frozen=True)
class RecoveryChecks:
    exchange_connected: bool
    balances_synced: bool
    positions_reconciled: bool
    open_orders_reconciled: bool
    risk_limits_valid: bool
    market_data_healthy: bool

class RecoveryManager:
    def __init__(self, confirmations_required=3):
        if confirmations_required <= 0: raise ValueError("confirmations_required must be positive")
        self.confirmations_required=confirmations_required; self.state=RecoveryState.TRIPPED; self.confirmations=0
    def diagnose(self, checks: RecoveryChecks):
        if all((checks.exchange_connected,checks.balances_synced,checks.positions_reconciled,checks.open_orders_reconciled,checks.risk_limits_valid,checks.market_data_healthy)):
            self.state=RecoveryState.SAFE; self.confirmations=0
        else: self.state=RecoveryState.FAILED; self.confirmations=0
        return self.state
    def confirm_safe(self):
        if self.state != RecoveryState.SAFE: return self.state
        self.confirmations += 1
        if self.confirmations >= self.confirmations_required: self.state=RecoveryState.PAPER
        return self.state
    def authorize_live(self):
        if self.state != RecoveryState.PAPER: raise RuntimeError("live trading requires confirmed paper recovery")
        self.state=RecoveryState.LIVE
        return self.state
