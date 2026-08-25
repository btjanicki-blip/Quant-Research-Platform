"""Matplotlib reporting adapter for completed backtests."""

from __future__ import annotations

from collections.abc import Sequence
from itertools import pairwise
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..core.models import Bar, Side

if TYPE_CHECKING:
    from ..core.engine import BacktestResult


def _matplotlib() -> tuple[Any, Any]:
    try:
        import matplotlib.dates as mdates
        import matplotlib.pyplot as plt
    except ImportError as error:
        raise ImportError(
            "Backtest charts require matplotlib. Install it with "
            "`python -m pip install -e '.[visualization]'`."
        ) from error
    return plt, mdates


def _maximum_drawdown_interval(equity: Sequence[float]) -> tuple[int, int]:
    """Return the peak and trough indices for the largest peak-to-trough loss."""
    if not equity:
        raise ValueError("equity must not be empty")
    peak_index = 0
    maximum_peak_index = 0
    trough_index = 0
    worst_drawdown = 0.0
    for index, value in enumerate(equity):
        if value > equity[peak_index]:
            peak_index = index
        drawdown = value / equity[peak_index] - 1.0 if equity[peak_index] else 0.0
        if drawdown < worst_drawdown:
            worst_drawdown = drawdown
            maximum_peak_index = peak_index
            trough_index = index
    return maximum_peak_index, trough_index


def plot_backtest_report(
    result: BacktestResult,
    bars: Sequence[Bar],
    *,
    symbol: str | None = None,
    title: str | None = None,
    output_path: str | Path | None = None,
    show: bool = True,
) -> Any:
    """Create a compact visual report for a completed backtest.

    The report includes price and fill markers, equity with the maximum drawdown
    interval highlighted, per-period returns, a drawdown series, and key metrics.
    A single-symbol bar series is inferred when ``symbol`` is omitted.
    """
    if not result.equity_curve:
        raise ValueError("cannot plot a backtest with an empty equity curve")
    if not bars:
        raise ValueError("cannot plot a backtest without bars")

    selected_symbol = symbol or bars[0].symbol
    selected_bars = [bar for bar in bars if bar.symbol == selected_symbol]
    if not selected_bars:
        raise ValueError(f"no bars found for symbol {selected_symbol!r}")

    plt, mdates = _matplotlib()
    timestamps = [point.timestamp for point in result.equity_curve]
    equity = [point.equity for point in result.equity_curve]
    running_peak: list[float] = []
    peak = equity[0]
    for value in equity:
        peak = max(peak, value)
        running_peak.append(peak)
    drawdowns = [(value / high - 1.0) if high else 0.0 for value, high in zip(equity, running_peak)]
    returns = [0.0] + [later / earlier - 1.0 if earlier else 0.0 for earlier, later in pairwise(equity)]

    peak_index, trough_index = _maximum_drawdown_interval(equity)

    figure = plt.figure(figsize=(14, 10), constrained_layout=True)
    grid = figure.add_gridspec(3, 2, height_ratios=(3, 2, 1.1))
    price_axis = figure.add_subplot(grid[0, 0])
    equity_axis = figure.add_subplot(grid[0, 1])
    returns_axis = figure.add_subplot(grid[1, 0], sharex=equity_axis)
    drawdown_axis = figure.add_subplot(grid[1, 1], sharex=equity_axis)
    metrics_axis = figure.add_subplot(grid[2, :])

    bar_times = [bar.timestamp for bar in selected_bars]
    closes = [bar.close for bar in selected_bars]
    price_axis.plot(bar_times, closes, color="#1f77b4", label=f"{selected_symbol} close")
    fills = [fill for fill in result.fills if fill.symbol == selected_symbol]
    for side, marker, color, label in ((Side.BUY, "^", "#2ca02c", "Buy"), (Side.SELL, "v", "#d62728", "Sell")):
        side_fills = [fill for fill in fills if fill.side is side]
        if side_fills:
            price_axis.scatter([fill.timestamp for fill in side_fills], [fill.price for fill in side_fills],
                               marker=marker, color=color, s=55, label=label, zorder=3)
    price_axis.set_title("Price and fills")
    price_axis.set_ylabel("Price")
    price_axis.legend(loc="best")

    equity_axis.plot(timestamps, equity, color="#1f77b4", label="Equity")
    equity_axis.plot(timestamps, running_peak, color="#7f7f7f", linewidth=1, label="Running peak")
    if peak_index < trough_index:
        equity_axis.axvspan(timestamps[peak_index], timestamps[trough_index], color="#d62728", alpha=0.12,
                            label="Maximum drawdown")
    equity_axis.set_title("Equity and maximum drawdown")
    equity_axis.set_ylabel("Equity")
    equity_axis.legend(loc="best")

    returns_axis.bar(timestamps, returns, width=0.8, color=["#2ca02c" if value >= 0 else "#d62728" for value in returns])
    returns_axis.axhline(0, color="#7f7f7f", linewidth=0.8)
    returns_axis.set_title("Per-period returns")
    returns_axis.set_ylabel("Return")
    returns_axis.yaxis.set_major_formatter(lambda value, _: f"{value:.1%}")

    drawdown_axis.fill_between(timestamps, drawdowns, 0, color="#d62728", alpha=0.25)
    drawdown_axis.plot(timestamps, drawdowns, color="#d62728")
    drawdown_axis.set_title("Drawdown")
    drawdown_axis.set_ylabel("Drawdown")
    drawdown_axis.yaxis.set_major_formatter(lambda value, _: f"{value:.1%}")

    for axis in (price_axis, equity_axis, returns_axis, drawdown_axis):
        axis.grid(alpha=0.25)
        axis.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        for label in axis.get_xticklabels():
            label.set_rotation(30)
            label.set_ha("right")

    performance = result.performance
    attribution = result.trade_attribution
    metrics_axis.axis("off")
    metrics = (
        f"Total return  {performance.total_return:.2%}     "
        f"Annualized volatility  {performance.annualized_volatility:.2%}     "
        f"Sharpe  {performance.sharpe_ratio:.2f}     "
        f"Max drawdown  {performance.max_drawdown:.2%}\n"
        f"Fills  {performance.fill_count}     "
        f"Closed trades  {len(attribution.trades)}     "
        f"Win rate  {attribution.win_rate:.2%}     "
        f"Expectancy  {attribution.expectancy:.2f}     "
        f"Profit factor  {attribution.profit_factor:.2f}"
    )
    metrics_axis.text(0.01, 0.88, metrics, transform=metrics_axis.transAxes, va="top", fontsize=11,
                      bbox={"boxstyle": "round,pad=0.6", "facecolor": "#f4f4f4", "edgecolor": "#bbbbbb"})
    figure.suptitle(title or f"Backtest report: {selected_symbol}", fontsize=16)

    if output_path is not None:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(destination, dpi=160, bbox_inches="tight")
    if show:
        plt.show()
    return figure
