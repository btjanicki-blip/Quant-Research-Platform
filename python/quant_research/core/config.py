from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class BacktestConfig:
    initial_cash: float = 100_000.0
    run_id: str = "unnamed"
    random_seed: int = 0
    annual_risk_free_rate: float = 0.0
    liquidate_at_end: bool = True
    tags: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.initial_cash <= 0:
            raise ValueError("initial_cash must be positive")
        if self.annual_risk_free_rate <= -1:
            raise ValueError("annual_risk_free_rate must be greater than -100%")
