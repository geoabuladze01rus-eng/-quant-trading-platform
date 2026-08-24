"""Global risk circuit breaker. Fail closed: any triggered condition blocks new orders."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class RiskTelemetry:
    daily_pnl: Decimal
    max_daily_loss: Decimal
    slippage_bps: Decimal
    max_slippage_bps: Decimal
    exchange_connected: bool
    balance_in_sync: bool
    failed_executions: int
    max_failed_executions: int

@dataclass(frozen=True)
class CircuitState:
    tripped: bool
    reason: str

class CircuitBreaker:
    def evaluate(self,t):
        if t.daily_pnl <= -abs(t.max_daily_loss): return CircuitState(True,"daily_loss_limit")
        if t.slippage_bps > t.max_slippage_bps: return CircuitState(True,"excessive_slippage")
        if not t.exchange_connected: return CircuitState(True,"exchange_disconnected")
        if not t.balance_in_sync: return CircuitState(True,"balance_desync")
        if t.failed_executions >= t.max_failed_executions: return CircuitState(True,"execution_failure_limit")
        return CircuitState(False,"clear")
