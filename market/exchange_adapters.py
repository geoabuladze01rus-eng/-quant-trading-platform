"""Pure parsers for normalized market data from Binance/Bybit/OKX payloads.
Network/WebSocket transport is intentionally kept separate.
"""
from market.normalized_orderbook import OrderBookNormalizer, NormalizedOrderBook

class BinanceAdapter:
    venue = "BINANCE"
    def parse_book(self, payload: dict) -> NormalizedOrderBook:
        return OrderBookNormalizer.normalize(self.venue, payload["s"], int(payload.get("E", 0)), payload.get("b", []), payload.get("a", []), payload.get("u"))

class BybitAdapter:
    venue = "BYBIT"
    def parse_book(self, payload: dict) -> NormalizedOrderBook:
        data = payload.get("data", payload)
        symbol = data.get("s") or data.get("symbol")
        bids = data.get("b", data.get("bids", [])); asks = data.get("a", data.get("asks", []))
        return OrderBookNormalizer.normalize(self.venue, symbol, int(payload.get("ts", data.get("ts", 0))), bids, asks, data.get("u", data.get("seq")))

class OkxAdapter:
    venue = "OKX"
    def parse_book(self, payload: dict) -> NormalizedOrderBook:
        data = payload.get("data", [payload])[0]
        return OrderBookNormalizer.normalize(self.venue, data.get("instId") or data.get("symbol"), int(data.get("ts", 0)), data.get("bids", []), data.get("asks", []), data.get("seqId"))
