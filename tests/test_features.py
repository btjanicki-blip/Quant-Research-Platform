from datetime import datetime, timedelta
from unittest import TestCase

from quant_research.core.models import Bar
from quant_research.data.features import FeaturePipeline, Returns, RollingMean


class FeaturePipelineTest(TestCase):
    def test_features_are_streamed_and_maintain_separate_symbol_state(self) -> None:
        start = datetime(2025, 1, 1)
        bars = [
            Bar(start, "A", 10, 10, 10, 10, 1),
            Bar(start + timedelta(days=1), "B", 100, 100, 100, 100, 1),
            Bar(start + timedelta(days=2), "A", 12, 12, 12, 12, 1),
        ]
        rows = list(FeaturePipeline([RollingMean(2), Returns()]).transform(bars))
        self.assertIsNone(rows[0].values["mean_close_2"])
        self.assertIsNone(rows[1].values["return_1"])
        self.assertEqual(rows[2].values["mean_close_2"], 11)
        self.assertAlmostEqual(rows[2].values["return_1"], 0.2)
