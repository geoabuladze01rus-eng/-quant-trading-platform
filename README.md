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
3. `reconcile_group` finalizes the two primary legs after their orders have
   filled, closed, or been cancelled. Equal full or partial fills complete as a
   balanced group; unequal fills expose a signed residual and require a hedge.
4. `hedge_residual` creates and fills a risk-reducing paper order. The default
   guardrails cap hedge notional at 10,000 and adverse slippage at 30 bps. A
   breach halts both primary legs instead of issuing the hedge.

Every transition and fill is retained in the canonical event journal with its
timestamp, correlation ID, execution group ID, order fields, and fill fields.
The canonical path has no live-order method and does not call authenticated
exchange connectors.

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
