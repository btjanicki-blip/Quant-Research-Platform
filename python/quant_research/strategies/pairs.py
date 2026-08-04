from __future__ import annotations

from collections import defaultdict

from ..core.interfaces import OrderSink
from ..core.models import Bar, Fill, Order, Side
from ..statistics.indicators import zscore


class PairsTradingStrategy:
    """Dollar-neutral spread strategy with explicit entry/exit thresholds.

    The hedge ratio is fixed by configuration; estimating it is a separate research step,
    preventing in-sample parameter fitting from being hidden in the trading loop.
    """
    def __init__(self, left: str, right: str, hedge_ratio: float, window: int, quantity: float,
                 entry_z: float = 2.0, exit_z: float = 0.5) -> None:
        if left == right or hedge_ratio <= 0 or window < 2 or quantity <= 0 or entry_z <= exit_z:
            raise ValueError("invalid pairs configuration")
        self._left, self._right = left, right
        self._hedge, self._window, self._quantity = hedge_ratio, window, quantity
        self._entry, self._exit = entry_z, exit_z
        self._prices: dict[str, dict[str, float]] = defaultdict(dict)
        self._spreads: list[float] = []
        self._orders: OrderSink | None = None
        self._state = 0  # 1: long spread; -1: short spread

    def initialize(self, orders: OrderSink) -> None:
        self._orders = orders

    def on_data(self, bar: Bar) -> None:
        if bar.symbol not in (self._left, self._right):
            return
        bucket = self._prices[bar.timestamp.isoformat()]
        bucket[bar.symbol] = bar.close
        if self._left not in bucket or self._right not in bucket:
            return
        self._spreads.append(bucket[self._left] - self._hedge * bucket[self._right])
        score = zscore(self._spreads, self._window)
        if score is None:
            return
        target = 1 if score <= -self._entry else -1 if score >= self._entry else 0 if abs(score) <= self._exit else self._state
        if target != self._state:
            self._rebalance(target, bar.timestamp)
            self._state = target

    def _rebalance(self, target: int, timestamp) -> None:
        assert self._orders is not None
        # Changing from ±1 to ∓1 correctly submits the full two-unit target delta.
        left_delta = (target - self._state) * self._quantity
        right_delta = -(target - self._state) * self._quantity * self._hedge
        if left_delta:
            self._orders.submit(Order(self._left, Side.BUY if left_delta > 0 else Side.SELL, abs(left_delta), timestamp))
        if right_delta:
            self._orders.submit(Order(self._right, Side.BUY if right_delta > 0 else Side.SELL, abs(right_delta), timestamp))

    def on_fill(self, fill: Fill) -> None:
        pass

    def on_finish(self) -> None:
        pass
