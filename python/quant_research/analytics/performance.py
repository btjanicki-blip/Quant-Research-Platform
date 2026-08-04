from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ..core.models import EquityPoint, Fill
from ..risk.metrics import summarize_risk


@dataclass(frozen=True, slots=True)
class PerformanceSummary:
    total_return: float
    annualized_volatility: float
    sharpe_ratio: float
    max_drawdown: float
    fill_count: int
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    value_at_risk_95: float = 0.0
    expected_shortfall_95: float = 0.0
    average_gross_exposure: float = 0.0


def summarize(curve: Sequence[EquityPoint], fills: Sequence[Fill], periods_per_year: int = 252) -> PerformanceSummary:
    if len(curve) < 2:
        return PerformanceSummary(0.0, 0.0, 0.0, 0.0, len(fills))
    returns = [later.equity / earlier.equity - 1 for earlier, later in zip(curve, curve[1:]) if earlier.equity]
    risk = summarize_risk(returns, [point.equity for point in curve], periods_per_year)
    volatility = (sum((item - sum(returns) / len(returns)) ** 2 for item in returns) / len(returns)) ** 0.5 * periods_per_year ** 0.5 if returns else 0.0
    average_exposure = sum(point.gross_exposure / point.equity for point in curve if point.equity) / len(curve)
    return PerformanceSummary(curve[-1].equity / curve[0].equity - 1, volatility, risk.sharpe_ratio,
                              risk.maximum_drawdown, len(fills), risk.sortino_ratio, risk.calmar_ratio,
                              risk.value_at_risk, risk.expected_shortfall, average_exposure)
