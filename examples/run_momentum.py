from datetime import datetime, timedelta

from quant_research.core.config import BacktestConfig
from quant_research.core.engine import BacktestEngine
from quant_research.core.models import Bar
from quant_research.data.sources import InMemoryBarSource
from quant_research.execution.simulator import BarExecutionModel
from quant_research.portfolio.portfolio import Portfolio
from quant_research.strategies.moving_average import MovingAverageCrossStrategy

start = datetime(2025, 1, 1)
prices = [100 + i * 0.3 + (i % 5 - 2) * 0.4 for i in range(60)]
bars = [Bar(start + timedelta(days=i), "DEMO", price, price + 1, price - 1, price, 50_000)
        for i, price in enumerate(prices)]
config = BacktestConfig(run_id="momentum-demo")
result = BacktestEngine(InMemoryBarSource(bars), MovingAverageCrossStrategy("DEMO", 5, 20, 100),
                        BarExecutionModel(), Portfolio(config.initial_cash), config).run()
print(result.performance)
