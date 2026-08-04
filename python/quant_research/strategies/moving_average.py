from __future__ import annotations

from ..core.interfaces import OrderSink
from ..core.models import Bar, Fill, Order, Side
from ..statistics.indicators import rolling_mean


class MovingAverageCrossStrategy:
    """Target-position strategy used as an intentionally transparent reference implementation."""

    def __init__(self, symbol: str, fast_window: int, slow_window: int, quantity: float) -> None:
        if not 0 < fast_window < slow_window or quantity <= 0:
            raise ValueError("require 0 < fast_window < slow_window and positive quantity")
        self._symbol, self._fast, self._slow, self._quantity = symbol, fast_window, slow_window, quantity
        self._prices: list[float] = []
        self._orders: OrderSink | None = None
        self._target = 0.0

    def initialize(self, orders: OrderSink) -> None:
        self._orders = orders

    def on_data(self, bar: Bar) -> None:
        if bar.symbol != self._symbol:
            return
        self._prices.append(bar.close)
        fast, slow = rolling_mean(self._prices, self._fast), rolling_mean(self._prices, self._slow)
        if fast is None or slow is None:
            return
        target = self._quantity if fast > slow else 0.0
        delta = target - self._target
        if delta:
            assert self._orders is not None
            self._orders.submit(Order(bar.symbol, Side.BUY if delta > 0 else Side.SELL, abs(delta), bar.timestamp))
            self._target = target

    def on_fill(self, fill: Fill) -> None:
        pass

    def on_finish(self) -> None:
        pass
