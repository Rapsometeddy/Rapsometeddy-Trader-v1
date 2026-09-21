"""Historical backtest runner."""
import pandas as pd
from bot.paper_trader import PaperTrader
from bot.strategy import add_indicators, generate_signal

def run(df: pd.DataFrame, balance: float) -> PaperTrader:
    data = add_indicators(df)
    trader = PaperTrader(balance)
    for _, row in data.iterrows():
        trader.check_exit(float(row["high"]), float(row["low"]))
        if trader.position is None:
            signal = generate_signal(row)
            if signal in ("BUY", "SELL"):
                trader.open(signal, float(row["close"]))
    if trader.position is not None:
        trader.close(float(data.iloc[-1]["close"]), "END_OF_TEST")
    return trader
