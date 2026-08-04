from __future__ import annotations

import math
import random
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConfidenceInterval:
    mean: float
    lower: float
    upper: float


@dataclass(frozen=True, slots=True)
class HypothesisTest:
    statistic: float
    p_value: float


def mean_confidence_interval(values: Sequence[float], confidence: float = 0.95) -> ConfidenceInterval:
    if len(values) < 2 or not 0 < confidence < 1:
        raise ValueError("at least two values and confidence in (0, 1) are required")
    mean = sum(values) / len(values)
    deviation = math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))
    # Normal critical values are a transparent dependency-free approximation for daily-return samples.
    critical = 1.96 if confidence == 0.95 else _inverse_normal_cdf((1 + confidence) / 2)
    margin = critical * deviation / math.sqrt(len(values))
    return ConfidenceInterval(mean, mean - margin, mean + margin)


def one_sample_z_test(values: Sequence[float], null_mean: float = 0.0) -> HypothesisTest:
    if len(values) < 2:
        raise ValueError("at least two values are required")
    mean = sum(values) / len(values)
    deviation = math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))
    statistic = (mean - null_mean) / (deviation / math.sqrt(len(values))) if deviation else 0.0
    p_value = math.erfc(abs(statistic) / math.sqrt(2))
    return HypothesisTest(statistic, p_value)


def monte_carlo_equity_paths(initial_equity: float, returns: Sequence[float], paths: int = 1_000,
                             seed: int = 0) -> tuple[tuple[float, ...], ...]:
    if initial_equity <= 0 or not returns or paths <= 0:
        raise ValueError("initial_equity, returns, and paths must be positive/non-empty")
    generator = random.Random(seed)
    simulations = []
    for _ in range(paths):
        equity, path = initial_equity, [initial_equity]
        for _ in returns:
            equity *= 1 + generator.choice(returns)
            path.append(equity)
        simulations.append(tuple(path))
    return tuple(simulations)


def _inverse_normal_cdf(probability: float) -> float:
    # Acklam rational approximation, adequate for research reporting quantiles.
    if not 0 < probability < 1:
        raise ValueError("probability must be in (0, 1)")
    # A bisection method using erfc is short, stable, and avoids hard-coded polynomial tables.
    low, high = -8.0, 8.0
    for _ in range(80):
        midpoint = (low + high) / 2
        cdf = 0.5 * math.erfc(-midpoint / math.sqrt(2))
        if cdf < probability:
            low = midpoint
        else:
            high = midpoint
    return (low + high) / 2
