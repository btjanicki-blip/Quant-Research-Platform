from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from ..core.models import EquityPoint, Fill


@dataclass(frozen=True, slots=True)
class PerformanceSummary:
    total_return: float
    annualized_volatility: float
    sharpe_ratio: float
    max_drawdown: float
    fill_count: int


def summarize(curve: Sequence[EquityPoint], fills: Sequence[Fill], periods_per_year: int = 252) -> PerformanceSummary:
    if len(curve) < 2:
        return PerformanceSummary(0.0, 0.0, 0.0, 0.0, len(fills))
    returns = [later.equity / earlier.equity - 1 for earlier, later in zip(curve, curve[1:]) if earlier.equity]
    mean = sum(returns) / len(returns) if returns else 0.0
    variance = sum((item - mean) ** 2 for item in returns) / len(returns) if returns else 0.0
    volatility = math.sqrt(variance) * math.sqrt(periods_per_year)
    sharpe = mean / math.sqrt(variance) * math.sqrt(periods_per_year) if variance else 0.0
    peak, maximum_drawdown = curve[0].equity, 0.0
    for point in curve:
        peak = max(peak, point.equity)
        maximum_drawdown = min(maximum_drawdown, point.equity / peak - 1)
    return PerformanceSummary(curve[-1].equity / curve[0].equity - 1, volatility, sharpe,
                              maximum_drawdown, len(fills))
