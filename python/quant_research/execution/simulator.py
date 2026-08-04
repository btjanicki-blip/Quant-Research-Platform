from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Protocol

from ..core.models import Bar, Fill, Order, OrderStatus, Side


class SlippageModel(Protocol):
    def price(self, bar: Bar, side: Side) -> float: ...


class CommissionModel(Protocol):
    def cost(self, quantity: float, price: float) -> float: ...


@dataclass(frozen=True, slots=True)
class FixedBpsSlippage:
    basis_points: float = 1.0

    def price(self, bar: Bar, side: Side) -> float:
        return bar.close * (1 + side.sign * self.basis_points / 10_000)


@dataclass(frozen=True, slots=True)
class PerShareCommission:
    rate: float = 0.005
    minimum: float = 0.0

    def cost(self, quantity: float, price: float) -> float:
        return max(self.minimum, quantity * self.rate)


class BarExecutionModel:
    """Conservative bar-level market execution with latency and volume participation caps."""

    def __init__(self, slippage: SlippageModel | None = None, commission: CommissionModel | None = None,
                 participation_rate: float = 0.10, latency_bars: int = 0) -> None:
        if not 0 < participation_rate <= 1 or latency_bars < 0:
            raise ValueError("invalid execution configuration")
        self._slippage = slippage or FixedBpsSlippage()
        self._commission = commission or PerShareCommission()
        self._participation, self._latency = participation_rate, latency_bars
        self._pending: deque[tuple[Order, int]] = deque()

    def submit(self, order: Order) -> None:
        self._pending.append((order, self._latency))

    def process_bar(self, bar: Bar) -> list[Fill]:
        fills: list[Fill] = []
        retained: deque[tuple[Order, int]] = deque()
        capacity = bar.volume * self._participation
        while self._pending:
            order, bars_remaining = self._pending.popleft()
            if order.symbol != bar.symbol or bars_remaining > 0:
                retained.append((order, max(0, bars_remaining - 1)))
                continue
            quantity = min(order.remaining_quantity, capacity)
            if quantity <= 0:
                retained.append((order, 0))
                continue
            price = self._slippage.price(bar, order.side)
            fill = Fill(order.id, order.symbol, order.side, quantity, price, bar.timestamp,
                        self._commission.cost(quantity, price))
            order.filled_quantity += quantity
            order.status = OrderStatus.FILLED if order.remaining_quantity == 0 else OrderStatus.PARTIALLY_FILLED
            fills.append(fill)
            capacity -= quantity
            if order.remaining_quantity > 0:
                retained.append((order, 0))
        self._pending = retained
        return fills
