from datetime import datetime
from math import isclose
from unittest import TestCase

from quant_research.core.models import Fill, Side
from quant_research.portfolio.portfolio import Portfolio


class PortfolioTest(TestCase):
    def test_tracks_realized_and_unrealized_accounting(self) -> None:
        portfolio = Portfolio(1_000)
        now = datetime(2025, 1, 1)
        portfolio.apply_fill(Fill("a", "ABC", Side.BUY, 10, 100, now, 1))
        portfolio.apply_fill(Fill("b", "ABC", Side.SELL, 4, 110, now, 1))
        position = portfolio.positions["ABC"]
        self.assertTrue(isclose(portfolio.cash, 438))
        self.assertEqual(position.quantity, 6)
        self.assertEqual(position.average_price, 100)
        self.assertTrue(isclose(position.realized_pnl, 40))
        self.assertTrue(isclose(portfolio.snapshot(now, {"ABC": 105}).equity, 1_068))
