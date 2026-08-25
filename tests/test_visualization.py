from datetime import UTC, datetime, timedelta
from importlib import import_module

import pytest
from quant_research.core.config import BacktestConfig
from quant_research.core.engine import BacktestEngine
from quant_research.core.models import Bar, Order, Side
from quant_research.data.sources import InMemoryBarSource
from quant_research.execution.simulator import BarExecutionModel
from quant_research.portfolio.portfolio import Portfolio
from quant_research.visualization import plot_backtest_report
from quant_research.visualization.backtest import _maximum_drawdown_interval, _per_period_returns

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg", force=True)
plt = import_module("matplotlib.pyplot")


START = datetime(2025, 1, 1, tzinfo=UTC)


class BuyThenSell:
    def initialize(self, engine):
        self.engine = engine

    def on_data(self, bar):
        day = (bar.timestamp - START).days
        if day == 0:
            self.engine.submit(Order("ABC", Side.BUY, 1, bar.timestamp))
        if day == 2:
            self.engine.submit(Order("ABC", Side.SELL, 1, bar.timestamp))

    def on_fill(self, fill):
        pass

    def on_finish(self):
        pass


def test_plot_backtest_report_saves_all_requested_panels(tmp_path) -> None:
    prices = [100, 102, 98, 101, 103]
    bars = [Bar(START + timedelta(days=index), "ABC", price, price + 1, price - 1, price, 1_000)
            for index, price in enumerate(prices)]
    result = BacktestEngine(InMemoryBarSource(bars), BuyThenSell(), BarExecutionModel(), Portfolio(1_000),
                            BacktestConfig()).run()

    output = tmp_path / "backtest-report.png"
    figure = plot_backtest_report(result, bars, output_path=output, show=False)

    assert output.exists()
    assert output.stat().st_size > 0
    assert [axis.get_title() for axis in figure.axes[:4]] == [
        "Price and fills", "Equity and maximum drawdown", "Per-period returns", "Drawdown",
    ]
    plt.close(figure)


def test_drawdown_interval_uses_the_peak_that_precedes_the_worst_trough() -> None:
    # The initial pullback is not the maximum drawdown; the band must start at 120.
    assert _maximum_drawdown_interval([100, 95, 120, 100, 105]) == (2, 3)


def test_return_series_keeps_zero_values_for_flat_periods() -> None:
    assert _per_period_returns([1_000, 1_000, 1_010, 1_010]) == pytest.approx([0.0, 0.0, 0.01, 0.0])
