from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import uuid4


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"

    @property
    def sign(self) -> int:
        return 1 if self is Side.BUY else -1


class OrderStatus(str, Enum):
    NEW = "new"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class Bar:
    timestamp: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float

    def __post_init__(self) -> None:
        if self.low > min(self.open, self.close) or self.high < max(self.open, self.close):
            raise ValueError("OHLC values are inconsistent")
        if self.volume < 0:
            raise ValueError("volume cannot be negative")


@dataclass(slots=True)
class Order:
    symbol: str
    side: Side
    quantity: float
    submitted_at: datetime
    id: str = field(default_factory=lambda: uuid4().hex)
    filled_quantity: float = 0.0
    status: OrderStatus = OrderStatus.NEW

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("order quantity must be positive")

    @property
    def remaining_quantity(self) -> float:
        return self.quantity - self.filled_quantity


@dataclass(frozen=True, slots=True)
class Fill:
    order_id: str
    symbol: str
    side: Side
    quantity: float
    price: float
    timestamp: datetime
    commission: float = 0.0

    def __post_init__(self) -> None:
        if self.quantity <= 0 or self.price <= 0 or self.commission < 0:
            raise ValueError("invalid fill")


@dataclass(frozen=True, slots=True)
class EquityPoint:
    timestamp: datetime
    equity: float
    cash: float
    gross_exposure: float
