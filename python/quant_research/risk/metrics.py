from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RiskMetrics:
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    value_at_risk: float
    expected_shortfall: float
    maximum_drawdown: float


def maximum_drawdown(equity: Sequence[float]) -> float:
    if not equity:
        return 0.0
    peak, drawdown = equity[0], 0.0
    for value in equity:
        peak = max(peak, value)
        if peak:
            drawdown = min(drawdown, value / peak - 1)
    return drawdown


def value_at_risk(returns: Sequence[float], confidence: float = 0.95) -> float:
    """Historical VaR reported as a positive loss fraction."""
    _validate_confidence(confidence)
    if not returns:
        return 0.0
    index = max(0, math.ceil((1 - confidence) * len(returns)) - 1)
    return max(0.0, -sorted(returns)[index])


def expected_shortfall(returns: Sequence[float], confidence: float = 0.95) -> float:
    _validate_confidence(confidence)
    if not returns:
        return 0.0
    count = max(1, math.ceil((1 - confidence) * len(returns)))
    return max(0.0, -sum(sorted(returns)[:count]) / count)


def summarize_risk(returns: Sequence[float], equity: Sequence[float], periods_per_year: int = 252,
                   confidence: float = 0.95, annual_risk_free_rate: float = 0.0) -> RiskMetrics:
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    if annual_risk_free_rate <= -1:
        raise ValueError("annual_risk_free_rate must be greater than -100%")
    # Returns are logarithmic. Subtract the matching per-period log risk-free rate
    # before annualising excess-return statistics.
    risk_free_per_period = math.log1p(annual_risk_free_rate) / periods_per_year
    excess_returns = [item - risk_free_per_period for item in returns]
    mean = sum(excess_returns) / len(excess_returns) if excess_returns else 0.0
    variance = (sum((item - mean) ** 2 for item in excess_returns) / (len(excess_returns) - 1)
                if len(excess_returns) > 1 else 0.0)
    deviation = math.sqrt(variance)
    downside = (math.sqrt(sum(min(item, 0) ** 2 for item in excess_returns) / len(excess_returns))
                if excess_returns else 0.0)
    drawdown = maximum_drawdown(equity)
    annual_return = math.exp(mean * periods_per_year) - 1
    return RiskMetrics(
        sharpe_ratio=mean / deviation * math.sqrt(periods_per_year) if deviation else 0.0,
        sortino_ratio=mean / downside * math.sqrt(periods_per_year) if downside else 0.0,
        calmar_ratio=annual_return / abs(drawdown) if drawdown else 0.0,
        value_at_risk=value_at_risk(excess_returns, confidence),
        expected_shortfall=expected_shortfall(excess_returns, confidence),
        maximum_drawdown=drawdown,
    )


def _validate_confidence(confidence: float) -> None:
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between zero and one")
