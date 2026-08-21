# Cryptohopper benchmark and product requirements

Research date: 2026-08-21.

## Product lessons

Cryptohopper combines automated trading, copy trading, strategies, AI-assisted strategy switching, trailing features, stop-loss, take-profit, DCA, exchange arbitrage, market making, paper trading, strategy design, backtesting and a marketplace. It supports web plus iOS/Android and connects to exchanges without taking custody of funds.

## User pain points to design against

1. Setup complexity: provide a guided wizard, preflight diagnostics and plain-language explanations for every blocked order.
2. Opaque execution: every signal must expose signal time, decision, reason, expected fill, actual fill, fees, slippage, latency and rejection reason.
3. Weak visibility: provide live charts with strategy buy/sell events, open positions, order state and realized/unrealized P&L.
4. Cost/value concerns: transparent pricing, generous paper trading and backtesting; core functionality should not depend on paid signals.
5. Marketplace quality: verified statistics, drawdown, sample size, age, fees, risk score and out-of-sample performance; automatically flag stale strategies.
6. DCA risk: hard exposure caps, regime filters, maximum rescue attempts and kill conditions; never imply guaranteed recovery.
7. Mobile UX: mobile must be a first-class monitoring and control surface.
8. Exchange/quote mismatches: preflight balances, permissions, symbols, quote currency, minimum order size and API capabilities before activation.
9. Support: actionable diagnostics and exportable incident reports, with clear human escalation.
10. Profit expectations: show risk-adjusted results and clearly distinguish backtest, paper and live performance; never promise profit.

## Product requirements

### Beginner mode
- Goal-based onboarding: capital, risk, exchanges and desired activity.
- One-click paper trading first.
- Bot health score and "why no trade?" explanation.
- Safe defaults and mandatory risk limits.
- No leverage by default.

### Pro mode
- Strategy designer.
- Multi-exchange arbitrage.
- Backtesting and walk-forward validation.
- Paper/live comparison.
- Custom indicators and webhooks.
- Portfolio-level risk engine.

### Observability
- Event-sourced trade journal.
- Full order lifecycle.
- Live P&L and drawdown.
- Slippage/latency/fee attribution.
- Exchange health and data-quality score.
- Strategy attribution.

### Marketplace
- Verified strategy profiles.
- Standardized metrics and confidence intervals.
- Out-of-sample results.
- Strategy versioning.
- Automatic stale-performance warnings.
- No hidden performance claims.
- Clear subscription and total-cost disclosure.

### Safety
- Trading-only API permissions where possible; withdrawals disabled.
- Encrypted secrets and IP allowlisting where supported.
- Kill switch and daily loss/exposure limits.
- Circuit breakers for stale data, abnormal spreads, exchange outages and fill imbalance.
- Paper mode and sandbox before live activation.

## Differentiation target

Do not build a clone. Target Cryptohopper breadth plus institutional-grade execution/risk transparency and dramatically simpler onboarding. The promise is understandable automation, not guaranteed profit.
