import json
from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from quant_research.analytics.attribution import TradeAttribution
from quant_research.analytics.performance import PerformanceSummary
from quant_research.core.config import BacktestConfig
from quant_research.core.experiments import JsonlExperimentTracker


class ExperimentTrackerTest(TestCase):
    def test_tracker_writes_append_only_jsonl_events(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "runs.jsonl"
            tracker = JsonlExperimentTracker(path)
            tracker.started(BacktestConfig(run_id="test", tags=("unit",)))
            tracker.completed(PerformanceSummary(0, 0, 0, 0, 0), TradeAttribution((), 0, 0, 0, timedelta()))
            records = [json.loads(line) for line in path.read_text().splitlines()]
        self.assertEqual([record["event"] for record in records], ["started", "completed"])
        self.assertEqual(records[0]["config"]["run_id"], "test")
