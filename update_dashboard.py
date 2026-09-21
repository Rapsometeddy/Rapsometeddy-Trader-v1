"""Generate dashboard data from the educational demo backtest."""
import json
from pathlib import Path
import pandas as pd

from config import INITIAL_BALANCE, FAST_EMA, SLOW_EMA, RSI_PERIOD
from bot.strategy import add_indicators, generate_signal
from backtest.engine import run
from backtest.metrics import calculate_metrics
from run_backtest import make_demo_data

def main():
    raw = make_demo_data()
    data = add_indicators(raw)
    trader = run(raw, INITIAL_BALANCE)
    m = calculate_metrics(trader)

    equity = [m.starting_balance]
    history = []
    for number, trade in enumerate(trader.trades, start=1):
        equity.append(equity[-1] + trade.pnl)
        history.append({
            "number": number, "side": trade.side, "entry": trade.entry,
            "exit": trade.exit, "quantity": trade.quantity,
            "pnl": trade.pnl, "reason": trade.reason,
        })

    candles = []
    for _, row in data.iterrows():
        candles.append({
            "open": float(row["open"]), "high": float(row["high"]),
            "low": float(row["low"]), "close": float(row["close"]),
            "ema_fast": None if pd.isna(row["ema_fast"]) else float(row["ema_fast"]),
            "ema_slow": None if pd.isna(row["ema_slow"]) else float(row["ema_slow"]),
            "rsi": None if pd.isna(row["rsi"]) else float(row["rsi"]),
            "signal": generate_signal(row),
        })

    result = {
        "starting_balance": m.starting_balance, "ending_balance": m.ending_balance,
        "total_pnl": m.total_pnl, "return_pct": m.return_pct,
        "trades": m.trades, "winning_trades": m.winning_trades,
        "losing_trades": m.losing_trades, "win_rate_pct": m.win_rate_pct,
        "max_drawdown_pct": m.max_drawdown_pct, "equity_curve": equity,
        "trade_history": history, "candles": candles,
        "settings": {"fast_ema": FAST_EMA, "slow_ema": SLOW_EMA, "rsi_period": RSI_PERIOD},
    }
    Path("dashboard/data.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
