from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class BacktestConfig:
    initial_cash: float = 100_000.0
    run_id: str = "unnamed"
    random_seed: int = 0
    tags: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.initial_cash <= 0:
            raise ValueError("initial_cash must be positive")
