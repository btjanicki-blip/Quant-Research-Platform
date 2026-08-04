from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from ..analytics.attribution import TradeAttribution
from ..analytics.performance import PerformanceSummary
from .config import BacktestConfig


class ExperimentTracker(Protocol):
    def started(self, config: BacktestConfig) -> None: ...
    def completed(self, performance: PerformanceSummary, attribution: TradeAttribution) -> None: ...


class JsonlExperimentTracker:
    """Append-only local experiment ledger suitable for reproducible research runs."""
    def __init__(self, path: str | Path, logger: logging.Logger | None = None) -> None:
        self._path, self._logger = Path(path), logger or logging.getLogger(__name__)

    def started(self, config: BacktestConfig) -> None:
        self._record("started", {"config": asdict(config)})

    def completed(self, performance: PerformanceSummary, attribution: TradeAttribution) -> None:
        self._record("completed", {"performance": asdict(performance), "closed_trade_count": len(attribution.trades),
                                    "win_rate": attribution.win_rate, "expectancy": attribution.expectancy})

    def _record(self, event: str, payload: dict[str, object]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        record = {"timestamp": datetime.now(UTC).isoformat(), "event": event, **payload}
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, default=str, sort_keys=True) + "\n")
        self._logger.info("experiment_event=%s run_id=%s", event, payload.get("config", {}).get("run_id", "-"))
