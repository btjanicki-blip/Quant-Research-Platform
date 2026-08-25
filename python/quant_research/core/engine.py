from __future__ import annotations

from dataclasses import dataclass

from ..analytics.attribution import TradeAttribution, summarize_trades
from ..analytics.performance import PerformanceSummary, summarize
from ..portfolio.portfolio import Portfolio
from .config import BacktestConfig
from .experiments import ExperimentTracker
from .interfaces import ExecutionModel, MarketDataSource, Strategy
from .models import Bar, EquityPoint, Fill, Order


@dataclass(frozen=True, slots=True)
class BacktestResult:
    equity_curve: tuple[EquityPoint, ...]
    fills: tuple[Fill, ...]
    performance: PerformanceSummary
    trade_attribution: TradeAttribution
    open_positions: tuple[tuple[str, float], ...] = ()


class BacktestEngine:
    """Coordinates deterministic event ordering; collaborators own their own domain logic."""

    def __init__(
        self, data: MarketDataSource, strategy: Strategy, execution: ExecutionModel,
        portfolio: Portfolio, config: BacktestConfig, tracker: ExperimentTracker | None = None,
    ) -> None:
        self._data, self._strategy = data, strategy
        self._execution, self._portfolio, self._config = execution, portfolio, config
        self._tracker = tracker
        self._fills: list[Fill] = []
        self._marks: dict[str, float] = {}

    def submit(self, order: Order) -> None:
        self._execution.submit(order)

    def run(self) -> BacktestResult:
        if self._tracker:
            self._tracker.started(self._config)
        self._strategy.initialize(self)
        curve: list[EquityPoint] = []
        previous_timestamp = None
        last_bars: dict[str, Bar] = {}
        for bar in self._data.bars():
            if previous_timestamp and bar.timestamp < previous_timestamp:
                raise ValueError("market data must be time ordered")
            previous_timestamp = bar.timestamp
            self._marks[bar.symbol] = bar.close
            last_bars[bar.symbol] = bar
            # Fills precede the strategy callback: submitted orders cannot fill on the same bar.
            for fill in self._execution.process_bar(bar):
                self._portfolio.apply_fill(fill)
                self._strategy.on_fill(fill)
                self._fills.append(fill)
            self._strategy.on_data(bar)
            curve.append(self._portfolio.snapshot(bar.timestamp, self._marks))
        self._strategy.on_finish()
        if curve and self._config.liquidate_at_end:
            self._liquidate_positions(last_bars, curve)
        fills = tuple(self._fills)
        open_positions = tuple((symbol, position.quantity) for symbol, position in self._portfolio.positions.items()
                               if position.quantity)
        result = BacktestResult(tuple(curve), fills,
                                summarize(curve, fills, annual_risk_free_rate=self._config.annual_risk_free_rate),
                                summarize_trades(fills), open_positions)
        if self._tracker:
            self._tracker.completed(result.performance, result.trade_attribution)
        return result

    def _liquidate_positions(self, last_bars: dict[str, Bar], curve: list[EquityPoint]) -> None:
        """Close every residual position and replace the final marked snapshot."""
        for symbol, position in tuple(self._portfolio.positions.items()):
            if not position.quantity:
                continue
            bar = last_bars.get(symbol)
            if bar is None:
                raise ValueError(f"cannot liquidate {symbol!r}: no final market bar")
            fill = self._execution.close_position(symbol, position.quantity, bar)
            self._portfolio.apply_fill(fill)
            self._strategy.on_fill(fill)
            self._fills.append(fill)
            self._marks[symbol] = fill.price
        curve[-1] = self._portfolio.snapshot(curve[-1].timestamp, self._marks)
