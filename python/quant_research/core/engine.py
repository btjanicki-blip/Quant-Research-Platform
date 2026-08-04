from __future__ import annotations

from dataclasses import dataclass

from ..analytics.performance import PerformanceSummary, summarize
from ..portfolio.portfolio import Portfolio
from .config import BacktestConfig
from .interfaces import ExecutionModel, MarketDataSource, Strategy
from .models import EquityPoint, Fill, Order


@dataclass(frozen=True, slots=True)
class BacktestResult:
    equity_curve: tuple[EquityPoint, ...]
    fills: tuple[Fill, ...]
    performance: PerformanceSummary


class BacktestEngine:
    """Coordinates deterministic event ordering; collaborators own their own domain logic."""

    def __init__(
        self, data: MarketDataSource, strategy: Strategy, execution: ExecutionModel,
        portfolio: Portfolio, config: BacktestConfig,
    ) -> None:
        self._data, self._strategy = data, strategy
        self._execution, self._portfolio, self._config = execution, portfolio, config
        self._fills: list[Fill] = []
        self._marks: dict[str, float] = {}

    def submit(self, order: Order) -> None:
        self._execution.submit(order)

    def run(self) -> BacktestResult:
        self._strategy.initialize(self)
        curve: list[EquityPoint] = []
        previous_timestamp = None
        for bar in self._data.bars():
            if previous_timestamp and bar.timestamp < previous_timestamp:
                raise ValueError("market data must be time ordered")
            previous_timestamp = bar.timestamp
            self._marks[bar.symbol] = bar.close
            # Fills precede the strategy callback: submitted orders cannot fill on the same bar.
            for fill in self._execution.process_bar(bar):
                self._portfolio.apply_fill(fill)
                self._strategy.on_fill(fill)
                self._fills.append(fill)
            self._strategy.on_data(bar)
            curve.append(self._portfolio.snapshot(bar.timestamp, self._marks))
        self._strategy.on_finish()
        return BacktestResult(tuple(curve), tuple(self._fills), summarize(curve, self._fills))
