from __future__ import annotations

import random
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class SearchResult:
    parameters: dict[str, object]
    score: float
    evaluations: int


def random_search(parameters: dict[str, Iterable[object]], objective: Callable[[dict[str, object]], float],
                  iterations: int, seed: int = 0) -> SearchResult:
    """Seeded search for reproducible research runs; candidates may be any finite iterable."""
    if iterations <= 0:
        raise ValueError("iterations must be positive")
    choices = {name: tuple(values) for name, values in parameters.items()}
    if not choices or any(not values for values in choices.values()):
        raise ValueError("each parameter must provide at least one candidate")
    generator = random.Random(seed)
    best_parameters: dict[str, object] | None = None
    best_score = float("-inf")
    for _ in range(iterations):
        candidate = {name: generator.choice(values) for name, values in choices.items()}
        score = objective(candidate)
        if score > best_score:
            best_parameters, best_score = candidate, score
    assert best_parameters is not None
    return SearchResult(best_parameters, best_score, iterations)


@dataclass(frozen=True, slots=True)
class WalkForwardFold:
    train_start: int
    train_end: int
    test_start: int
    test_end: int


def walk_forward_splits(observations: int, train_size: int, test_size: int, step: int | None = None,
                        anchored: bool = True) -> tuple[WalkForwardFold, ...]:
    if observations <= 0 or train_size <= 0 or test_size <= 0:
        raise ValueError("observations, train_size, and test_size must be positive")
    stride = step or test_size
    if stride <= 0:
        raise ValueError("step must be positive")
    folds: list[WalkForwardFold] = []
    train_start, train_end = 0, train_size
    while train_end + test_size <= observations:
        folds.append(WalkForwardFold(train_start, train_end, train_end, train_end + test_size))
        train_start = 0 if anchored else train_start + stride
        train_end += stride
    return tuple(folds)


def bootstrap_means(returns: Sequence[float], iterations: int = 1_000, seed: int = 0) -> tuple[float, ...]:
    if not returns or iterations <= 0:
        raise ValueError("returns and iterations must be non-empty/positive")
    generator = random.Random(seed)
    return tuple(sum(generator.choice(returns) for _ in returns) / len(returns) for _ in range(iterations))


@dataclass(frozen=True, slots=True)
class BootstrapValidation:
    mean: float
    lower_bound: float
    upper_bound: float
    probability_positive: float


def validate_bootstrap(returns: Sequence[float], iterations: int = 1_000, confidence: float = 0.95,
                       seed: int = 0) -> BootstrapValidation:
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between zero and one")
    samples = sorted(bootstrap_means(returns, iterations, seed))
    lower = int(((1 - confidence) / 2) * iterations)
    upper = min(iterations - 1, int(((1 + confidence) / 2) * iterations))
    return BootstrapValidation(sum(samples) / iterations, samples[lower], samples[upper],
                               sum(value > 0 for value in samples) / iterations)
