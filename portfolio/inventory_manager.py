"""Capital and inventory reservation for cross-venue arbitrage."""
from dataclasses import dataclass, field
from decimal import Decimal

@dataclass
class VenueInventory:
    balances: dict[str, Decimal] = field(default_factory=dict)
    reserved: dict[str, Decimal] = field(default_factory=dict)
    def available(self, asset: str) -> Decimal:
        return self.balances.get(asset, Decimal("0")) - self.reserved.get(asset, Decimal("0"))

@dataclass(frozen=True)
class Reservation:
    venue: str
    asset: str
    amount: Decimal

class InventoryManager:
    def __init__(self):
        self.venues: dict[str, VenueInventory] = {}
        self.reservations: list[Reservation] = []
    def set_balance(self, venue: str, asset: str, amount: Decimal) -> None:
        if amount < 0: raise ValueError("balance cannot be negative")
        self.venues.setdefault(venue, VenueInventory()).balances[asset] = amount
    def available(self, venue: str, asset: str) -> Decimal:
        return self.venues.get(venue, VenueInventory()).available(asset)
    def reserve(self, venue: str, asset: str, amount: Decimal) -> Reservation:
        if amount <= 0: raise ValueError("reservation must be positive")
        if self.available(venue, asset) < amount: raise ValueError("insufficient available balance")
        inv = self.venues.setdefault(venue, VenueInventory())
        inv.reserved[asset] = inv.reserved.get(asset, Decimal("0")) + amount
        reservation = Reservation(venue, asset, amount)
        self.reservations.append(reservation)
        return reservation
    def release(self, reservation: Reservation) -> None:
        inv = self.venues[reservation.venue]
        current = inv.reserved.get(reservation.asset, Decimal("0"))
        if current < reservation.amount: raise ValueError("reservation exceeds reserved amount")
        inv.reserved[reservation.asset] = current - reservation.amount
        if inv.reserved[reservation.asset] == 0: del inv.reserved[reservation.asset]
        self.reservations.remove(reservation)
    def max_arbitrage_quantity(self, buy_venue: str, quote_asset: str, buy_price: Decimal, sell_venue: str, base_asset: str, requested_qty: Decimal) -> Decimal:
        if buy_price <= 0 or requested_qty <= 0: return Decimal("0")
        quote_capacity = self.available(buy_venue, quote_asset) / buy_price
        base_capacity = self.available(sell_venue, base_asset)
        return min(requested_qty, quote_capacity, base_capacity)
