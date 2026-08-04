from __future__ import annotations

import math
from collections.abc import Sequence


def rolling_mean(values: Sequence[float], window: int) -> float | None:
    if window <= 0:
        raise ValueError("window must be positive")
    return sum(values[-window:]) / window if len(values) >= window else None


def rolling_std(values: Sequence[float], window: int) -> float | None:
    mean = rolling_mean(values, window)
    if mean is None:
        return None
    return math.sqrt(sum((value - mean) ** 2 for value in values[-window:]) / window)


def ema(values: Sequence[float], window: int) -> float | None:
    if window <= 0:
        raise ValueError("window must be positive")
    if len(values) < window:
        return None
    alpha = 2 / (window + 1)
    result = sum(values[:window]) / window
    for value in values[window:]:
        result = alpha * value + (1 - alpha) * result
    return result


def rsi(values: Sequence[float], window: int = 14) -> float | None:
    if len(values) <= window:
        return None
    changes = [b - a for a, b in zip(values[-window - 1:-1], values[-window:])]
    gains = sum(max(change, 0) for change in changes) / window
    losses = sum(max(-change, 0) for change in changes) / window
    if losses == 0:
        return 100.0
    return 100 - 100 / (1 + gains / losses)


def simple_returns(values: Sequence[float]) -> list[float]:
    """One-period arithmetic returns, preserving no look-ahead convention."""
    return [current / previous - 1 for previous, current in zip(values, values[1:]) if previous != 0]


def log_returns(values: Sequence[float]) -> list[float]:
    if any(value <= 0 for value in values):
        raise ValueError("log returns require strictly positive prices")
    return [math.log(current / previous) for previous, current in zip(values, values[1:])]


def vwap(high: Sequence[float], low: Sequence[float], close: Sequence[float], volume: Sequence[float]) -> float | None:
    if not (len(high) == len(low) == len(close) == len(volume)):
        raise ValueError("OHLCV sequences must have equal lengths")
    total_volume = sum(volume)
    if not total_volume:
        return None
    return sum(((h + l + c) / 3) * v for h, l, c, v in zip(high, low, close, volume)) / total_volume


def atr(high: Sequence[float], low: Sequence[float], close: Sequence[float], window: int = 14) -> float | None:
    if not (len(high) == len(low) == len(close)):
        raise ValueError("OHLC sequences must have equal lengths")
    if len(close) <= window:
        return None
    ranges = [max(h - l, abs(h - prior), abs(l - prior))
              for h, l, prior in zip(high[1:], low[1:], close[:-1])]
    return rolling_mean(ranges, window)


def realized_volatility(values: Sequence[float], window: int, periods_per_year: int = 252) -> float | None:
    returns = log_returns(values)
    deviation = rolling_std(returns, window)
    return deviation * math.sqrt(periods_per_year) if deviation is not None else None


def zscore(values: Sequence[float], window: int) -> float | None:
    mean, deviation = rolling_mean(values, window), rolling_std(values, window)
    if mean is None or deviation is None:
        return None
    return 0.0 if deviation == 0 else (values[-1] - mean) / deviation


def rolling_correlation(left: Sequence[float], right: Sequence[float], window: int) -> float | None:
    if len(left) != len(right):
        raise ValueError("sequences must have equal lengths")
    if window <= 1 or len(left) < window:
        return None
    x, y = left[-window:], right[-window:]
    x_mean, y_mean = sum(x) / window, sum(y) / window
    covariance = sum((a - x_mean) * (b - y_mean) for a, b in zip(x, y)) / window
    x_std = math.sqrt(sum((a - x_mean) ** 2 for a in x) / window)
    y_std = math.sqrt(sum((b - y_mean) ** 2 for b in y) / window)
    return None if x_std == 0 or y_std == 0 else covariance / (x_std * y_std)


def beta(asset_returns: Sequence[float], benchmark_returns: Sequence[float]) -> float | None:
    if len(asset_returns) != len(benchmark_returns) or len(asset_returns) < 2:
        return None
    mean_asset = sum(asset_returns) / len(asset_returns)
    mean_benchmark = sum(benchmark_returns) / len(benchmark_returns)
    variance = sum((value - mean_benchmark) ** 2 for value in benchmark_returns) / len(benchmark_returns)
    if variance == 0:
        return None
    covariance = sum((asset - mean_asset) * (benchmark - mean_benchmark)
                     for asset, benchmark in zip(asset_returns, benchmark_returns)) / len(asset_returns)
    return covariance / variance
