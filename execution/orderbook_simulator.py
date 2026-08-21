"""Order-book execution model with partial fills and market impact."""
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class BookLevel:
    price: Decimal
    quantity: Decimal

@dataclass(frozen=True)
class BookExecution:
    requested: Decimal
    filled: Decimal
    notional: Decimal
    average_price: Decimal
    remaining: Decimal
    levels_consumed: int

class OrderBookSimulator:
    def execute(self, side: str, quantity: Decimal, asks: list[BookLevel], bids: list[BookLevel]) -> BookExecution:
        quantity=Decimal(str(quantity))
        if quantity<=0: raise ValueError("quantity must be positive")
        levels=asks if side.upper()=="BUY" else bids
        levels=sorted(levels,key=lambda x:x.price,reverse=side.upper()=="SELL")
        remaining=quantity; notional=Decimal("0"); filled=Decimal("0"); consumed=0
        for level in levels:
            if level.price<=0 or level.quantity<0: raise ValueError("invalid book level")
            take=min(remaining,level.quantity)
            if take>0:
                notional+=take*level.price; filled+=take; remaining-=take; consumed+=1
            if remaining==0: break
        avg=notional/filled if filled else Decimal("0")
        return BookExecution(quantity,filled,notional,avg,remaining,consumed)
