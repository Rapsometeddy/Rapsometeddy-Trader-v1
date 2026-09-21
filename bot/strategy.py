"""Signal generation for the paper-trading strategy."""
import pandas as pd
from config import FAST_EMA, SLOW_EMA, RSI_PERIOD
from .indicators import ema, rsi

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ema_fast"] = ema(out["close"], FAST_EMA)
    out["ema_slow"] = ema(out["close"], SLOW_EMA)
    out["rsi"] = rsi(out["close"], RSI_PERIOD)
    return out

def generate_signal(row: pd.Series) -> str:
    if pd.isna(row["ema_fast"]) or pd.isna(row["ema_slow"]) or pd.isna(row["rsi"]):
        return "HOLD"
    if row["ema_fast"] > row["ema_slow"] and row["rsi"] >= 50:
        return "BUY"
    if row["ema_fast"] < row["ema_slow"] and row["rsi"] <= 50:
        return "SELL"
    return "HOLD"
