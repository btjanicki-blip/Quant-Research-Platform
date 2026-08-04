from collections.abc import Callable, Iterable
from itertools import product
from typing import TypeVar

T = TypeVar("T")


def grid_search(parameters: dict[str, Iterable[T]], objective: Callable[[dict[str, T]], float]) -> tuple[dict[str, T], float]:
    """Deterministic baseline optimiser; keeps experiment generation independent of engine."""
    names, values = tuple(parameters), tuple(tuple(value) for value in parameters.values())
    if not names or any(not choices for choices in values):
        raise ValueError("each parameter must provide at least one candidate")
    candidates = ({name: value for name, value in zip(names, choice)} for choice in product(*values))
    return max(((candidate, objective(candidate)) for candidate in candidates), key=lambda item: item[1])
