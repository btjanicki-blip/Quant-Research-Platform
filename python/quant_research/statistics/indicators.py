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
