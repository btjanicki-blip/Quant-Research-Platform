from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Protocol

from ..core.models import Bar


class Feature(Protocol):
    """A stateful, per-symbol feature. `None` signals the warm-up period."""
    @property
    def name(self) -> str: ...
    def update(self, bar: Bar) -> float | None: ...


@dataclass(frozen=True, slots=True)
class FeatureRow:
    bar: Bar
    values: dict[str, float | None]


class FeaturePipeline:
    """Applies stateful features once per incoming bar, without materialising the data feed."""
    def __init__(self, features: Iterable[Feature]) -> None:
        self._features = tuple(features)
        names = [feature.name for feature in self._features]
        if len(names) != len(set(names)):
            raise ValueError("feature names must be unique")

    def transform(self, bars: Iterable[Bar]) -> Iterator[FeatureRow]:
        for bar in bars:
            yield FeatureRow(bar, {feature.name: feature.update(bar) for feature in self._features})


class RollingMean:
    def __init__(self, window: int, field: str = "close", name: str | None = None) -> None:
        if window <= 0:
            raise ValueError("window must be positive")
        self._window, self._field = window, field
        self._name = name or f"mean_{field}_{window}"
        self._values: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=window))

    @property
    def name(self) -> str:
        return self._name

    def update(self, bar: Bar) -> float | None:
        try:
            value = float(getattr(bar, self._field))
        except AttributeError as error:
            raise ValueError(f"unsupported Bar field: {self._field}") from error
        values = self._values[bar.symbol]
        values.append(value)
        return sum(values) / self._window if len(values) == self._window else None


class Returns:
    def __init__(self, name: str = "return_1") -> None:
        self._name, self._previous = name, {}

    @property
    def name(self) -> str:
        return self._name

    def update(self, bar: Bar) -> float | None:
        prior = self._previous.get(bar.symbol)
        self._previous[bar.symbol] = bar.close
        return None if prior is None else bar.close / prior - 1
