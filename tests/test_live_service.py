from decimal import Decimal

from marketdata.live_service import LivePaperService
from strategies.inter_exchange_arbitrage import InterExchangeArbitrage


def test_live_service_detects_paper_opportunity():
    strategy = InterExchangeArbitrage({"binance": Decimal(0), "bybit": Decimal(0)}, slippage_bps=Decimal(0), latency_buffer_bps=Decimal(0), min_net_edge_bps=Decimal(1))
    service = LivePaperService(strategy)
    service.ingest("binance", {"s":"BTCUSDT","b":"100","a":"100","B":"1","A":"1","E":1000})
    service.ingest("bybit", {"ts":1000,"data":{"s":"BTCUSDT","b":"101","a":"101","B":"1","A":"1"}})
    assert len(service.opportunities) == 1
    assert service.opportunities[0].signal.buy_venue == "binance"
