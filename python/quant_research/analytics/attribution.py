from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..core.models import Fill, Side


@dataclass(frozen=True, slots=True)
class Trade:
    symbol: str
    side: Side
    quantity: float
    entry_price: float
    exit_price: float
    entry_time: datetime
    exit_time: datetime
    gross_pnl: float
    net_pnl: float

    @property
    def duration(self) -> timedelta:
        return self.exit_time - self.entry_time


@dataclass(frozen=True, slots=True)
class TradeAttribution:
    trades: tuple[Trade, ...]
    win_rate: float
    expectancy: float
    profit_factor: float
    average_holding_period: timedelta


@dataclass(frozen=True, slots=True)
class _Lot:
    side: Side
    quantity: float
    price: float
    timestamp: datetime
    commission_per_share: float


def reconstruct_trades(fills: Iterable[Fill]) -> tuple[Trade, ...]:
    """FIFO lot matching. Open lots remain intentionally absent from closed-trade attribution."""
    books: dict[str, deque[_Lot]] = defaultdict(deque)
    trades: list[Trade] = []
    for fill in fills:
        remaining = fill.quantity
        commission_per_share = fill.commission / fill.quantity
        book = books[fill.symbol]
        while remaining and book and book[0].side is not fill.side:
            entry = book[0]
            quantity = min(remaining, entry.quantity)
            gross = quantity * (fill.price - entry.price) * entry.side.sign
            net = gross - quantity * (entry.commission_per_share + commission_per_share)
            trades.append(Trade(fill.symbol, entry.side, quantity, entry.price, fill.price, entry.timestamp,
                                fill.timestamp, gross, net))
            remaining -= quantity
            if quantity == entry.quantity:
                book.popleft()
            else:
                book[0] = _Lot(entry.side, entry.quantity - quantity, entry.price, entry.timestamp,
                               entry.commission_per_share)
        if remaining:
            book.append(_Lot(fill.side, remaining, fill.price, fill.timestamp, commission_per_share))
    return tuple(trades)


def summarize_trades(fills: Sequence[Fill]) -> TradeAttribution:
    trades = reconstruct_trades(fills)
    if not trades:
        return TradeAttribution(trades, 0.0, 0.0, 0.0, timedelta(0))
    winners = [trade.net_pnl for trade in trades if trade.net_pnl > 0]
    losers = [trade.net_pnl for trade in trades if trade.net_pnl < 0]
    gross_profit, gross_loss = sum(winners), abs(sum(losers))
    return TradeAttribution(
        trades=trades,
        win_rate=len(winners) / len(trades),
        expectancy=sum(trade.net_pnl for trade in trades) / len(trades),
        profit_factor=gross_profit / gross_loss if gross_loss else float("inf") if gross_profit else 0.0,
        average_holding_period=sum((trade.duration for trade in trades), timedelta(0)) / len(trades),
    )
