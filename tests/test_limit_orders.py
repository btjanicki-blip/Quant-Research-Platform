from datetime import datetime
from unittest import TestCase

from quant_research.core.models import Bar, Order, OrderType, Side
from quant_research.execution.simulator import BarExecutionModel, FixedBpsSlippage


class LimitOrderTest(TestCase):
    def test_limit_order_waits_until_touched_and_receives_price_improvement(self) -> None:
        now = datetime(2025, 1, 1)
        model = BarExecutionModel(FixedBpsSlippage(0), participation_rate=1)
        order = Order("ABC", Side.BUY, 1, now, order_type=OrderType.LIMIT, limit_price=100)
        model.submit(order)
        self.assertEqual(model.process_bar(Bar(now, "ABC", 105, 106, 101, 104, 10)), [])
        fills = model.process_bar(Bar(now, "ABC", 99, 102, 98, 101, 10))
        self.assertEqual(fills[0].price, 99)

    def test_submission_order_is_fifo_when_bar_capacity_is_limited(self) -> None:
        now = datetime(2025, 1, 1)
        model = BarExecutionModel(FixedBpsSlippage(0), participation_rate=0.5)
        first, second = Order("ABC", Side.BUY, 4, now), Order("ABC", Side.BUY, 4, now)
        model.submit(first)
        model.submit(second)
        fills = model.process_bar(Bar(now, "ABC", 10, 10, 10, 10, 10))
        self.assertEqual([(fill.order_id, fill.quantity) for fill in fills], [(first.id, 4), (second.id, 1)])
