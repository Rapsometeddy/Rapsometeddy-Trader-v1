"""Position sizing and protective levels."""
from config import RISK_PER_TRADE, STOP_LOSS_PCT, TAKE_PROFIT_PCT

def position_size(balance: float, entry: float) -> float:
    if balance <= 0 or entry <= 0:
        return 0.0
    risk_cash = balance * RISK_PER_TRADE
    return risk_cash / (entry * STOP_LOSS_PCT)

def levels(entry: float, side: str) -> tuple[float, float]:
    if side == "BUY":
        return entry * (1 - STOP_LOSS_PCT), entry * (1 + TAKE_PROFIT_PCT)
    if side == "SELL":
        return entry * (1 + STOP_LOSS_PCT), entry * (1 - TAKE_PROFIT_PCT)
    raise ValueError("side must be BUY or SELL")
