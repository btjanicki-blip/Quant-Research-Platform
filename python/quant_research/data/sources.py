from __future__ import annotations

import csv
import math
import random
from collections.abc import Iterable, Iterator
from datetime import datetime, timedelta
from pathlib import Path

from ..core.models import Bar


def simulate_stochastic_volatility_bars(
    symbol: str,
    start: datetime,
    periods: int,
    *,
    initial_price: float = 100.0,
    annual_drift: float = 0.08,
    annual_volatility: float = 0.22,
    volatility_of_volatility: float = 0.35,
    mean_reversion: float = 3.0,
    volume_mean: float = 1_000_000.0,
    seed: int | None = None,
) -> tuple[Bar, ...]:
    """Generate reproducible daily OHLCV bars using mean-reverting stochastic volatility.

    This is intended for examples and tests where real data is unavailable; it avoids
    deterministic trends and preserves valid OHLC relationships.
    """
    if periods <= 0 or initial_price <= 0 or annual_volatility <= 0 or volume_mean <= 0:
        raise ValueError("periods, initial_price, annual_volatility, and volume_mean must be positive")
    if volatility_of_volatility < 0 or mean_reversion < 0:
        raise ValueError("volatility_of_volatility and mean_reversion cannot be negative")
    generator = random.Random(seed)
    price = initial_price
    volatility = annual_volatility
    dt = 1 / 252
    bars: list[Bar] = []
    timestamp = start
    for _ in range(periods):
        opening = price
        volatility *= math.exp(mean_reversion * math.log(annual_volatility / volatility) * dt
                               + volatility_of_volatility * math.sqrt(dt) * generator.gauss(0, 1))
        volatility = max(0.01, min(volatility, 3.0))
        log_return = ((annual_drift - 0.5 * volatility ** 2) * dt
                      + volatility * math.sqrt(dt) * generator.gauss(0, 1))
        close = opening * math.exp(log_return)
        intraday_range = abs(generator.gauss(0, 1)) * volatility * math.sqrt(dt)
        high = max(opening, close) * math.exp(intraday_range / 2)
        low = min(opening, close) * math.exp(-intraday_range / 2)
        volume = max(1.0, volume_mean * math.exp(0.30 * generator.gauss(0, 1)))
        bars.append(Bar(timestamp, symbol, opening, high, low, close, volume))
        price = close
        timestamp += timedelta(days=1)
        while timestamp.weekday() >= 5:
            timestamp += timedelta(days=1)
    return tuple(bars)


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


class TabularBarSource:
    """Lazy adapter for Parquet, Feather, and Arrow IPC files.

    The optional ``pyarrow`` dependency is imported only when this adapter is used,
    keeping the simulation core lightweight.
    """
    def __init__(self, path: str | Path, batch_size: int = 65_536) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        self._path, self._batch_size = Path(path), batch_size

    def bars(self) -> Iterator[Bar]:
        try:
            import pyarrow.dataset as ds
        except ImportError as error:
            raise ImportError("TabularBarSource requires `pip install .[data]`") from error
        formats = {".parquet": "parquet", ".feather": "ipc", ".arrow": "ipc", ".ipc": "ipc"}
        try:
            file_format = formats[self._path.suffix.lower()]
        except KeyError as error:
            raise ValueError("supported tabular formats are Parquet, Feather, and Arrow IPC") from error
        dataset = ds.dataset(self._path, format=file_format)
        required = ("timestamp", "symbol", "open", "high", "low", "close", "volume")
        available = set(dataset.schema.names)
        missing = set(required) - available
        if missing:
            raise ValueError(f"market-data table is missing columns: {sorted(missing)}")
        scanner = dataset.scanner(columns=required, batch_size=self._batch_size)
        for batch in scanner.to_batches():
            columns = {name: batch.column(index).to_pylist() for index, name in enumerate(required)}
            for index in range(batch.num_rows):
                timestamp = columns["timestamp"][index]
                if not isinstance(timestamp, datetime):
                    raise ValueError("timestamp column must be Arrow timestamp-compatible")
                yield Bar(timestamp, str(columns["symbol"][index]), float(columns["open"][index]),
                          float(columns["high"][index]), float(columns["low"][index]),
                          float(columns["close"][index]), float(columns["volume"][index]))


class FrameBarSource:
    """Adapter for pandas or Polars frames without making either a core dependency."""
    def __init__(self, frame: object) -> None:
        self._frame = frame

    def bars(self) -> Iterator[Bar]:
        if hasattr(self._frame, "to_dicts"):  # Polars
            records = self._frame.to_dicts()  # type: ignore[union-attr]
        elif hasattr(self._frame, "to_dict"):  # Pandas
            records = self._frame.to_dict("records")  # type: ignore[union-attr]
        else:
            raise TypeError("frame must be a pandas or Polars DataFrame")
        for row in records:
            timestamp = row["timestamp"]
            if hasattr(timestamp, "to_pydatetime"):
                timestamp = timestamp.to_pydatetime()
            if not isinstance(timestamp, datetime):
                raise ValueError("timestamp values must be datetime objects")
            yield Bar(timestamp, str(row["symbol"]), float(row["open"]), float(row["high"]),
                      float(row["low"]), float(row["close"]), float(row["volume"]))
