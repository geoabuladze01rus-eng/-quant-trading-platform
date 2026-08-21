# Market and broker integrations

## Current milestone

The research build normalizes best bid/ask data into the `Quote` domain model and keeps live order submission disabled.

### Binance Spot
- Public market-data REST: `GET /api/v3/ticker/bookTicker`.
- Public WebSocket: `<symbol>@bookTicker`.
- Market-data-only endpoints do not require API authentication.

### Bybit V5
- Public REST ticker: `GET /v5/market/tickers?category=spot&symbol=...`.
- Public WebSocket ticker/order-book streams are planned for the low-latency collector.

### OKX V5
- Public REST ticker: `GET /api/v5/market/ticker?instId=...`.
- Public WebSocket `tickers` channel is planned for the low-latency collector.

### T-Invest API
- Personal connector uses the user's Bearer token.
- T-Invest supports REST, gRPC and WebSocket; market-data streams include order book, trades, candles and last prices.
- Trading orders will be implemented through the private account connector after sandbox/paper validation.
- T-Invest data is not intended to be retransmitted as a public data service. The commercial architecture must therefore isolate personal account data from any public redistribution layer and be reviewed against current T-Bank terms before launch.

## Safety gate

No connector in this milestone may bypass `RiskEngine` or `PaperExecutionEngine`. Live execution requires a separate reviewed release, explicit configuration, venue-specific permissions and end-to-end reconciliation tests.
