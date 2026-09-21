"""Performance metrics for paper backtests."""
from dataclasses import dataclass
from .engine import run

@dataclass
class BacktestMetrics:
    starting_balance: float
    ending_balance: float
    total_pnl: float
    return_pct: float
    trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    max_drawdown_pct: float

def calculate_metrics(trader) -> BacktestMetrics:
    balance = trader.starting_balance
    equity = [balance]
    wins = 0
    losses = 0

    for trade in trader.trades:
        balance += trade.pnl
        equity.append(balance)
        if trade.pnl > 0:
            wins += 1
        elif trade.pnl < 0:
            losses += 1

    peak = equity[0]
    max_drawdown = 0.0
    for value in equity:
        peak = max(peak, value)
        if peak:
            max_drawdown = max(max_drawdown, (peak - value) / peak * 100)

    trades = len(trader.trades)
    win_rate = wins / trades * 100 if trades else 0.0

    return BacktestMetrics(
        starting_balance=trader.starting_balance,
        ending_balance=balance,
        total_pnl=balance - trader.starting_balance,
        return_pct=(balance / trader.starting_balance - 1) * 100 if trader.starting_balance else 0.0,
        trades=trades,
        winning_trades=wins,
        losing_trades=losses,
        win_rate_pct=win_rate,
        max_drawdown_pct=max_drawdown,
    )
