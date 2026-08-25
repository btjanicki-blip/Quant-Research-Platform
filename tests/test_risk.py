from unittest import TestCase

from quant_research.risk.metrics import expected_shortfall, maximum_drawdown, summarize_risk, value_at_risk


class RiskMetricsTest(TestCase):
    def test_historical_tail_metrics_and_drawdown(self) -> None:
        returns = [-0.10, -0.02, 0.01, 0.03]
        self.assertEqual(value_at_risk(returns, 0.75), 0.10)
        self.assertEqual(expected_shortfall(returns, 0.75), 0.10)
        self.assertAlmostEqual(maximum_drawdown([100, 120, 90, 110]), -0.25)
        report = summarize_risk(returns, [100, 120, 90, 110], confidence=0.75)
        self.assertEqual(report.value_at_risk, 0.10)

    def test_sharpe_uses_log_excess_returns(self) -> None:
        report = summarize_risk([0.01, 0.02, -0.01], [100, 101, 103, 102], periods_per_year=252,
                                annual_risk_free_rate=0.05)
        self.assertGreater(report.sharpe_ratio, 0)
        self.assertLess(report.sharpe_ratio, 20)
