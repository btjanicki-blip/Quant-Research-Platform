from unittest import TestCase

from quant_research.statistics.inference import mean_confidence_interval, monte_carlo_equity_paths, one_sample_z_test


class InferenceTest(TestCase):
    def test_confidence_test_and_monte_carlo_are_deterministic(self) -> None:
        values = [0.01, 0.02, 0.03, 0.02]
        interval = mean_confidence_interval(values)
        self.assertLess(interval.lower, interval.mean)
        self.assertLess(interval.mean, interval.upper)
        self.assertLess(one_sample_z_test(values).p_value, 0.05)
        first = monte_carlo_equity_paths(100, values, paths=3, seed=1)
        self.assertEqual(first, monte_carlo_equity_paths(100, values, paths=3, seed=1))
        self.assertEqual(len(first[0]), 5)
