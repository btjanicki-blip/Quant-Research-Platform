from unittest import TestCase

from quant_research.optimization.search import random_search, validate_bootstrap, walk_forward_splits


class OptimizationTest(TestCase):
    def test_random_search_is_seeded_and_reports_best_candidate(self) -> None:
        objective = lambda candidate: -abs(candidate["lookback"] - 4)  # noqa: E731
        first = random_search({"lookback": range(1, 8)}, objective, iterations=100, seed=3)
        second = random_search({"lookback": range(1, 8)}, objective, iterations=100, seed=3)
        self.assertEqual(first, second)
        self.assertEqual(first.parameters, {"lookback": 4})

    def test_walk_forward_folds_do_not_leak_test_data(self) -> None:
        folds = walk_forward_splits(20, train_size=8, test_size=4)
        self.assertEqual([(fold.train_end, fold.test_start, fold.test_end) for fold in folds],
                         [(8, 8, 12), (12, 12, 16), (16, 16, 20)])

    def test_bootstrap_validation_is_reproducible(self) -> None:
        first = validate_bootstrap([0.01, -0.01, 0.02], iterations=50, seed=42)
        self.assertEqual(first, validate_bootstrap([0.01, -0.01, 0.02], iterations=50, seed=42))
        self.assertGreater(first.probability_positive, 0)
