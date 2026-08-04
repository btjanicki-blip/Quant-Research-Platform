from __future__ import annotations

import csv
from collections.abc import Iterable, Iterator
from datetime import datetime
from pathlib import Path

from ..core.models import Bar


class InMemoryBarSource:
    def __init__(self, bars: Iterable[Bar]) -> None:
        self._bars = tuple(bars)

    def bars(self) -> Iterator[Bar]:
        yield from self._bars


class CsvBarSource:
    """Streaming CSV adapter; avoids materialising a full dataset."""

    def __init__(self, path: str | Path, timestamp_format: str = "%Y-%m-%dT%H:%M:%S") -> None:
        self._path, self._format = Path(path), timestamp_format

    def bars(self) -> Iterator[Bar]:
        with self._path.open(newline="") as handle:
            for row in csv.DictReader(handle):
                yield Bar(
                    timestamp=datetime.strptime(row["timestamp"], self._format), symbol=row["symbol"],
                    open=float(row["open"]), high=float(row["high"]), low=float(row["low"]),
                    close=float(row["close"]), volume=float(row["volume"]),
                )
