from ..analytics.attribution import TradeAttribution
from ..analytics.performance import PerformanceSummary


def render_summary(summary: PerformanceSummary) -> str:
    return (f"total_return={summary.total_return:.2%}\n"
            f"annualized_volatility={summary.annualized_volatility:.2%}\n"
            f"sharpe_ratio={summary.sharpe_ratio:.3f}\n"
            f"sortino_ratio={summary.sortino_ratio:.3f}\n"
            f"calmar_ratio={summary.calmar_ratio:.3f}\n"
            f"max_drawdown={summary.max_drawdown:.2%}\n"
            f"value_at_risk_95={summary.value_at_risk_95:.2%}\n"
            f"expected_shortfall_95={summary.expected_shortfall_95:.2%}\n"
            f"fill_count={summary.fill_count}")


def render_trade_attribution(attribution: TradeAttribution) -> str:
    return (f"closed_trades={len(attribution.trades)}\n"
            f"win_rate={attribution.win_rate:.2%}\n"
            f"expectancy_currency_per_trade=${attribution.expectancy:,.2f}\n"
            f"profit_factor={attribution.profit_factor:.3f}\n"
            f"average_holding_period={attribution.average_holding_period}")
