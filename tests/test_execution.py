from datetime import datetime
from math import isclose
from unittest import TestCase

from quant_research.core.models import Bar, Order, Side
from quant_research.execution.simulator import BarExecutionModel, FixedBpsSlippage, PerShareCommission


class ExecutionTest(TestCase):
    def test_applies_capacity_costs_and_partial_fill(self) -> None:
        now = datetime(2025, 1, 1)
        model = BarExecutionModel(FixedBpsSlippage(10), PerShareCommission(0.01), participation_rate=0.1, latency_bars=0)
        order = Order("ABC", Side.BUY, 15, now)
        model.submit(order)
        fills = model.process_bar(Bar(now, "ABC", 100, 101, 99, 100, 100))
        self.assertEqual(len(fills), 1)
        self.assertEqual(fills[0].quantity, 10)
        self.assertTrue(isclose(fills[0].price, 100.1))
        self.assertTrue(isclose(fills[0].commission, 0.1))
        self.assertEqual(order.remaining_quantity, 5)
