"""Live quote pipeline for paper-mode monitoring."""
from dataclasses import dataclass

from marketdata.adapters import BinanceAdapter, BybitAdapter, OKXAdapter, RawBookTicker
from marketdata.quality_guard import QuoteQualityGuard
from marketdata.replay_bus import MarketDataBus
from marketdata.ws_clients import BookTickerParser
from strategies.inter_exchange_arbitrage import InterExchangeArbitrage, Quote


@dataclass(frozen=True)
class PaperOpportunity:
    signal: object
    quotes: tuple[Quote, ...]

class LivePaperService:
    """Consumes normalized exchange ticks and emits opportunities; never places orders."""
    def __init__(self, strategy: InterExchangeArbitrage, guard: QuoteQualityGuard | None = None) -> None:
        self.strategy = strategy
        self.guard = guard or QuoteQualityGuard()
        self.bus: MarketDataBus[Quote] = MarketDataBus()
        self.latest: dict[tuple[str, str], Quote] = {}
        self.opportunities: list[PaperOpportunity] = []
        self.bus.subscribe(self._on_quote)

    def _on_quote(self, quote: Quote) -> None:
        now_ms = quote.timestamp_ms
        if not self.guard.valid(quote, now_ms):
            return
        self.latest[(quote.venue, quote.symbol)] = quote
        same_symbol = [q for q in self.latest.values() if q.symbol == quote.symbol]
        signal = self.strategy.scan(same_symbol, now_ms)
        if signal is not None:
            pair = tuple(q for q in same_symbol if q.venue in (signal.buy_venue, signal.sell_venue))
            self.opportunities.append(PaperOpportunity(signal, pair))

    def ingest(self, venue: str, payload: dict) -> None:
        parsers = {"binance": BookTickerParser.binance, "bybit": BookTickerParser.bybit, "okx": BookTickerParser.okx}
        adapters = {"binance": BinanceAdapter(), "bybit": BybitAdapter(), "okx": OKXAdapter()}
        raw: RawBookTicker = parsers[venue](payload)
        quote = adapters[venue].normalize(raw)
        self.bus.connected(venue)
        self.bus.message(venue, quote)
