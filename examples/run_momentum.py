import argparse
from datetime import UTC, datetime

from quant_research.core.config import BacktestConfig
from quant_research.core.engine import BacktestEngine
from quant_research.data.sources import InMemoryBarSource, simulate_stochastic_volatility_bars
from quant_research.execution.simulator import BarExecutionModel
from quant_research.portfolio.portfolio import Portfolio
from quant_research.strategies.moving_average import MovingAverageCrossStrategy


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a stochastic-volatility moving-average backtest.")
    parser.add_argument("--report", metavar="PATH", help="write a PNG visual report to PATH")
    args = parser.parse_args()

    start = datetime(2025, 1, 1, tzinfo=UTC)
    bars = simulate_stochastic_volatility_bars("DEMO", start, 252, seed=7)
    config = BacktestConfig(run_id="momentum-demo")
    result = BacktestEngine(InMemoryBarSource(bars), MovingAverageCrossStrategy("DEMO", 5, 20, 100),
                            BarExecutionModel(), Portfolio(config.initial_cash), config).run()
    print(result.performance)
    if args.report:
        from quant_research.visualization import plot_backtest_report
        plot_backtest_report(result, bars, output_path=args.report, show=False)
        print(f"Wrote visual report to {args.report}")


if __name__ == "__main__":
    main()
