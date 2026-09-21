"""Run a small deterministic paper-trading example."""
import pandas as pd

from config import INITIAL_BALANCE
from backtest.engine import run

def make_demo_data() -> pd.DataFrame:
    closes = [
        100, 101, 102, 103, 104, 103, 105, 106, 107, 108,
        107, 109, 110, 111, 112, 111, 113, 114, 115, 116,
        115, 114, 113, 112, 111, 110, 109, 108, 109, 110,
        111, 112, 113, 114, 115, 116, 117, 118, 117, 119,
        120, 121, 120, 119, 118, 117, 116, 115, 116, 117,
        118, 119, 120, 121, 122, 123, 122, 121, 120, 119,
    ]
    return pd.DataFrame({
        "open": closes,
        "high": [x * 1.01 for x in closes],
        "low": [x * 0.99 for x in closes],
        "close": closes,
    })

def main() -> None:
    trader = run(make_demo_data(), INITIAL_BALANCE)
    print(f"Starting balance: {trader.starting_balance:.2f}")
    print(f"Ending balance:   {trader.balance:.2f}")
    print(f"Trades:           {len(trader.trades)}")
    for trade in trader.trades:
        print(
            f"{trade.side:4} entry={trade.entry:.2f} "
            f"exit={trade.exit:.2f} pnl={trade.pnl:.2f} "
            f"reason={trade.reason}"
        )

if __name__ == "__main__":
    main()
