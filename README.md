# Quant Trading Platform

Private research and production platform for autonomous algorithmic trading.

## Product vision

The platform is being developed first as a private trading laboratory and later as a commercial SaaS product with web, iOS and Android clients.

## Current milestone: real-time paper trading

The first end-to-end loop is now implemented:

```text
Binance / Bybit / OKX WebSocket
              ↓
        Quote normalization
              ↓
          Freshness gate
              ↓
    Inter-exchange arbitrage
              ↓
          Risk Engine
              ↓
       Paper Execution
              ↓
          Audit Log
```

The runtime is **paper-only**. It does not submit live orders.

### Canonical execution lifecycle

`src/quant_platform/execution_orchestrator.py` is the canonical execution state
machine. `PaperExecutionEngine` is its only runtime facade; legacy execution
experiments are not wired into the real-time paper pipeline.

The paper lifecycle is explicit and terminal:

1. `submit` registers both arbitrage legs under one `execution_group_id`.
2. `process_fill` applies incremental fills, records cumulative quantity and
   weighted-average price, and safely ignores exact duplicate fill events.
3. `close_order` records `canceled` or `expired` for a primary leg that did not
   fill completely. `reconcile_group` refuses to run until both legs are either
   fully filled or explicitly closed. Equal full or partial fills complete as a
   balanced group; unequal fills expose a signed residual and require a hedge.
4. `hedge_residual` creates and fills a risk-reducing paper order. The default
   guardrails cap hedge notional at 10,000 and adverse slippage at 30 bps. A
   breach halts both primary legs instead of issuing the hedge.

Every transition and fill is retained in the canonical event journal with its
timestamp, correlation ID, execution group ID, order fields, and fill fields.
The canonical path has no live-order method and does not call authenticated
exchange connectors.

### Execution recovery

Canonical state can be checkpointed and restored without losing fill
idempotency or residual-hedge state:

```python
from pathlib import Path

from quant_platform.execution import PaperExecutionEngine
from quant_platform.execution_checkpoint import JsonExecutionCheckpointStore

store = JsonExecutionCheckpointStore(Path("runtime/execution.json"))
engine = PaperExecutionEngine(checkpoint_store=store)
# submit / fill / close / reconcile / hedge now save automatically
engine = PaperExecutionEngine.from_checkpoint_store(store)
```

The JSON checkpoint contains order intents, the complete event journal, fill
identifiers, execution-group membership and reconciliation results. Before use,
the loader validates state transitions, cumulative quantities, group links and
hedge references. The file store writes with mode `0600`, flushes data and uses
an atomic replacement so an interrupted write cannot expose a partial snapshot.
The default real-time paper runtime uses `runtime/execution.json`, restores it
on startup and continues automatic checkpointing after recovery. A corrupted
checkpoint stops startup instead of silently discarding execution state.

An execution watchdog expires open paper legs after five seconds and then
reconciles the two-leg group. It also closes an orphaned first leg left by an
interrupted two-leg submission. Any asymmetric fill is audited and remains in
`hedge_required`; the watchdog does not invent a hedge price without fresh
market data. These intervals and the checkpoint path can be configured with
`EXECUTION_TIMEOUT_SECONDS`, `TIMEOUT_SWEEP_INTERVAL_SECONDS` and
`EXECUTION_CHECKPOINT_PATH`.

Run locally after installing the development dependencies:

```bash
pip install -e ".[dev]"
pytest -q
ruff check .
quant-paper-live
```

Default paper configuration uses BTCUSDT, a 0.001 BTC test quantity, a $100,000 virtual portfolio and a 2-second decision cooldown. Quotes older than the scanner freshness threshold are ignored.

## Product principles

- automated execution with no emotional decisions;
- exchange/broker agnostic trading core;
- independent portfolio risk governor;
- paper trading before live trading;
- complete audit trail for every decision and order;
- API keys must never have withdrawal permission where the venue supports granular permissions.

## Initial venues

- Binance
- Bybit
- OKX
- T-Investments / Tinkoff Invest API

## Initial strategy roadmap

1. Inter-exchange arbitrage
2. Funding / spot-futures basis
3. Statistical arbitrage
4. Market making
5. Adaptive portfolio allocation

## Safety

This repository is initially a research/paper-trading system. No live trading is enabled by default. Cryptocurrency and securities trading involve substantial risk and do not guarantee profit.
