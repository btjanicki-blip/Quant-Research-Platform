from datetime import datetime, timedelta
from unittest import TestCase

from quant_research.core.config import BacktestConfig
from quant_research.core.engine import BacktestEngine
from quant_research.core.models import Bar, Order, Side
from quant_research.data.sources import InMemoryBarSource
from quant_research.execution.simulator import BarExecutionModel
from quant_research.portfolio.portfolio import Portfolio


class BuyOnce:
    def initialize(self, orders): self.orders = orders
    def on_data(self, bar):
        if bar.timestamp.day == 1: self.orders.submit(Order("ABC", Side.BUY, 1, bar.timestamp))
    def on_fill(self, fill): pass
    def on_finish(self): pass


class EngineTest(TestCase):
    def test_orders_do_not_fill_on_the_same_bar_as_strategy_signal(self) -> None:
        start = datetime(2025, 1, 1)
        bars = [Bar(start + timedelta(days=i), "ABC", 100 + i, 101 + i, 99 + i, 100 + i, 1000) for i in range(2)]
        result = BacktestEngine(InMemoryBarSource(bars), BuyOnce(), BarExecutionModel(latency_bars=0),
                                Portfolio(1_000), BacktestConfig()).run()
        self.assertEqual(len(result.fills), 2)
        self.assertEqual(result.fills[0].timestamp, bars[1].timestamp)
        self.assertEqual(result.fills[-1].side, Side.SELL)
        self.assertEqual(len(result.trade_attribution.trades), 1)

    def test_end_of_backtest_liquidation_includes_position_in_trade_metrics(self) -> None:
        start = datetime(2025, 1, 1)
        bars = [Bar(start + timedelta(days=i), "ABC", 100 + 10 * i, 101 + 10 * i, 99 + 10 * i,
                    100 + 10 * i, 1_000) for i in range(3)]
        result = BacktestEngine(InMemoryBarSource(bars), BuyOnce(), BarExecutionModel(), Portfolio(1_000),
                                BacktestConfig()).run()
        self.assertEqual(len(result.trade_attribution.trades), 1)
        self.assertGreater(result.trade_attribution.win_rate, 0)
        self.assertGreater(result.trade_attribution.expectancy, 0)
        self.assertGreater(result.trade_attribution.profit_factor, 1)
