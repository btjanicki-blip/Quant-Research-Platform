from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..core.models import EquityPoint, Fill


@dataclass(slots=True)
class Position:
    quantity: float = 0.0
    average_price: float = 0.0
    realized_pnl: float = 0.0


class Portfolio:
    def __init__(self, initial_cash: float) -> None:
        self.cash = initial_cash
        self.positions: dict[str, Position] = {}

    def apply_fill(self, fill: Fill) -> None:
        position = self.positions.setdefault(fill.symbol, Position())
        signed = fill.side.sign * fill.quantity
        old_quantity = position.quantity
        self.cash -= signed * fill.price + fill.commission
        if old_quantity == 0 or old_quantity * signed > 0:
            position.average_price = ((abs(old_quantity) * position.average_price + fill.quantity * fill.price)
                                      / (abs(old_quantity) + fill.quantity))
        else:
            closed = min(abs(old_quantity), fill.quantity)
            position.realized_pnl += closed * (fill.price - position.average_price) * (1 if old_quantity > 0 else -1)
            if abs(signed) > abs(old_quantity):
                position.average_price = fill.price
            elif abs(signed) == abs(old_quantity):
                position.average_price = 0.0
        position.quantity += signed

    def snapshot(self, timestamp: datetime, marks: dict[str, float]) -> EquityPoint:
        market_value = sum(p.quantity * marks.get(symbol, p.average_price) for symbol, p in self.positions.items())
        gross = sum(abs(p.quantity * marks.get(symbol, p.average_price)) for symbol, p in self.positions.items())
        return EquityPoint(timestamp, self.cash + market_value, self.cash, gross)
