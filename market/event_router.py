"""Route prioritized events into market state and risk intelligence."""
from dataclasses import dataclass, field
from decimal import Decimal

from core.event_bus import EventBus, EventPriority, PrioritizedEvent
from intelligence.event_impact_engine import EventImpact, EventImpactEngine, ImpactDirection


@dataclass
class MarketState:
    prices: dict[str, Decimal] = field(default_factory=dict)
    volatility: dict[str, Decimal] = field(default_factory=dict)
    risk_multiplier: Decimal = Decimal(1)
    last_impacts: list[EventImpact] = field(default_factory=list)

class MarketEventRouter:
    def __init__(self, bus=None, impact_engine=None):
        self.bus = bus or EventBus()
        self.impact_engine = impact_engine or EventImpactEngine()
        self.state = MarketState()

    def publish_market(self, event_type: str, symbol: str, payload: dict, priority: EventPriority = EventPriority.NORMAL):
        self.bus.publish(event_type, {"symbol": symbol, **payload}, priority)

    def publish_external(self, event_type: str, asset: str, confidence: Decimal, severity: Decimal, direction: ImpactDirection, reason: str = ""):
        priority = EventPriority.HIGH if severity < Decimal("0.9") else EventPriority.CRITICAL
        self.bus.publish("external_impact", {"event_type": event_type, "asset": asset, "confidence": confidence, "severity": severity, "direction": direction, "reason": reason}, priority)

    def process_next(self) -> PrioritizedEvent | None:
        event = self.bus.next()
        if event is None:
            return None
        payload = event.payload
        if event.event_type == "external_impact":
            impact = self.impact_engine.evaluate(**payload)
            self.state.risk_multiplier = min(self.state.risk_multiplier, impact.risk_multiplier)
            self.state.last_impacts.append(impact)
        elif "price" in payload and "symbol" in payload:
            self.state.prices[payload["symbol"]] = Decimal(str(payload["price"]))
        elif "volatility" in payload and "symbol" in payload:
            self.state.volatility[payload["symbol"]] = Decimal(str(payload["volatility"]))
        return event
