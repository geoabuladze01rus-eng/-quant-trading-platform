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
