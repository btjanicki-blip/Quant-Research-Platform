from datetime import datetime
from unittest import TestCase

from quant_research.core.models import Bar
from quant_research.strategies.pairs import PairsTradingStrategy


class Collector:
    def __init__(self) -> None:
        self.orders = []

    def submit(self, order) -> None:
        self.orders.append(order)


class PairsStrategyTest(TestCase):
    def test_strategy_enters_dollar_neutral_spread_on_extreme_zscore(self) -> None:
        strategy, orders = PairsTradingStrategy("LEFT", "RIGHT", 1, window=2, quantity=10, entry_z=1, exit_z=0.1), Collector()
        strategy.initialize(orders)
        timestamp = datetime(2025, 1, 1)
        for left, right in [(100, 100), (101, 100), (110, 100)]:
            strategy.on_data(Bar(timestamp, "LEFT", left, left, left, left, 100))
            strategy.on_data(Bar(timestamp, "RIGHT", right, right, right, right, 100))
        self.assertEqual({order.symbol for order in orders.orders}, {"LEFT", "RIGHT"})
