from dataclasses import dataclass

from ..core.models import Order


@dataclass(frozen=True, slots=True)
class MaxGrossExposure:
    """Pre-trade guard suitable for composing ahead of an execution adapter."""
    limit: float

    def validate(self, order: Order, mark_prices: dict[str, float]) -> bool:
        price = mark_prices.get(order.symbol)
        return price is not None and order.quantity * price <= self.limit
