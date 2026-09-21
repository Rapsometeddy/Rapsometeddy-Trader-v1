"""Generate dashboard metrics, equity curve, and trade history from the demo backtest."""
import json
from pathlib import Path

from config import INITIAL_BALANCE
from backtest.engine import run
from backtest.metrics import calculate_metrics
from run_backtest import make_demo_data

def main():
    trader = run(make_demo_data(), INITIAL_BALANCE)
    m = calculate_metrics(trader)

    equity = [m.starting_balance]
    history = []
    for number, trade in enumerate(trader.trades, start=1):
        equity.append(equity[-1] + trade.pnl)
        history.append({
            "number": number,
            "side": trade.side,
            "entry": trade.entry,
            "exit": trade.exit,
            "quantity": trade.quantity,
            "pnl": trade.pnl,
            "reason": trade.reason,
        })

    data = {
        "starting_balance": m.starting_balance,
        "ending_balance": m.ending_balance,
        "total_pnl": m.total_pnl,
        "return_pct": m.return_pct,
        "trades": m.trades,
        "winning_trades": m.winning_trades,
        "losing_trades": m.losing_trades,
        "win_rate_pct": m.win_rate_pct,
        "max_drawdown_pct": m.max_drawdown_pct,
        "equity_curve": equity,
        "trade_history": history,
    }
    Path("dashboard/data.json").write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    main()
