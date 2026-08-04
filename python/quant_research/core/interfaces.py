from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from .models import Bar, Fill, Order


class MarketDataSource(Protocol):
    def bars(self) -> Iterable[Bar]: ...


class OrderSink(Protocol):
    def submit(self, order: Order) -> None: ...


class Strategy(Protocol):
    def initialize(self, orders: OrderSink) -> None: ...
    def on_data(self, bar: Bar) -> None: ...
    def on_fill(self, fill: Fill) -> None: ...
    def on_finish(self) -> None: ...


class ExecutionModel(Protocol):
    def submit(self, order: Order) -> None: ...
    def process_bar(self, bar: Bar) -> list[Fill]: ...


class RiskPolicy(Protocol):
    def validate(self, order: Order, mark_prices: dict[str, float]) -> bool: ...
