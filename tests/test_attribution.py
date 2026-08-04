from datetime import datetime, timedelta
from unittest import TestCase

from quant_research.analytics.attribution import summarize_trades
from quant_research.core.models import Fill, Side


class AttributionTest(TestCase):
    def test_fifo_trade_attribution_accounts_for_both_side_commissions(self) -> None:
        opened = datetime(2025, 1, 1)
        fills = [
            Fill("one", "ABC", Side.BUY, 10, 100, opened, 1),
            Fill("two", "ABC", Side.SELL, 4, 110, opened + timedelta(days=3), 0.4),
        ]
        result = summarize_trades(fills)
        self.assertEqual(len(result.trades), 1)
        self.assertEqual(result.trades[0].gross_pnl, 40)
        self.assertAlmostEqual(result.trades[0].net_pnl, 39.2)
        self.assertEqual(result.win_rate, 1.0)
        self.assertEqual(result.average_holding_period, timedelta(days=3))
