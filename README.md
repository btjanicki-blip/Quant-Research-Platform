# Quant Research Platform

A modular, event-driven research and simulation platform intended to mirror the boundaries of a quantitative research stack: data ingestion, feature generation, signal creation, execution simulation, portfolio accounting, risk, and reporting.

## Principles

- **Explicit contracts:** small `Protocol` interfaces keep strategy, execution, data, and analytics components replaceable.
- **Reproducible experiments:** immutable run configuration and deterministic event ordering.
- **Correctness first:** cash, position, realized PnL, commissions, and equity are independently tracked and tested.
- **Progressive acceleration:** the Python orchestration layer has an optional pybind11 C++ matching-engine extension boundary.

## Quick start

```bash
python3 -m pip install -e '.[dev]'
PYTHONPATH=python python3 examples/run_momentum.py
PYTHONPATH=python python3 -m pytest
```

### Visual backtest report

Install the optional plotting dependency, then ask the momentum example to save a PNG report:

```bash
python3 -m pip install -e '.[dev,visualization]'
python3 examples/run_momentum.py --report reports/momentum-report.png
```

The report includes an equity curve with its maximum drawdown interval highlighted, price and buy/sell fill markers, per-period returns, drawdown, and a compact performance/trade summary.

## Layout

| Path | Responsibility |
| --- | --- |
| `python/quant_research/core` | Domain models, event bus, configuration, engine orchestration |
| `data`, `statistics`, `analytics` | Data adapters, indicators, risk/performance metrics |
| `strategies`, `execution`, `portfolio`, `risk` | Replaceable research and simulation policies |
| `cpp/matching_engine` | Optional performance-critical matching primitive via pybind11 |
| `tests` | Deterministic unit and integration tests |
| `configs`, `examples`, `docs` | Reproducible run inputs, demonstrations, architecture notes |

The current vertical slice supports OHLCV bars, CSV and lazy Arrow/Parquet/Feather ingestion, streaming feature pipelines, long/short market and limit orders, deterministic latency, FIFO submission priority, participation-limited partial fills, commission/slippage models, portfolio accounting with leverage/margin queries, risk-aware performance metrics (Sharpe, Sortino, Calmar, historical VaR/ES, drawdown, and exposure), FIFO trade attribution, market-neutral pairs trading, reproducible random/walk-forward/bootstrap validation, confidence intervals, hypothesis tests, Monte Carlo paths, and append-only experiment tracking. The interfaces are deliberately narrow so a quote-level limit-order-book simulator or institutional data adapter can be substituted without changing strategies.
