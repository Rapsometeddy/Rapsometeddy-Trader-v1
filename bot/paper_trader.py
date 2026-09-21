"""Simple paper-trading simulator."""
from dataclasses import dataclass
from .risk import levels, position_size

@dataclass
class Trade:
    side: str
    entry: float
    exit: float
    quantity: float
    pnl: float
    reason: str

class PaperTrader:
    def __init__(self, balance: float):
        self.starting_balance = balance
        self.balance = balance
        self.position = None
        self.trades: list[Trade] = []

    def open(self, side: str, price: float) -> None:
        if self.position is not None:
            return
        qty = position_size(self.balance, price)
        stop, target = levels(price, side)
        self.position = {"side": side, "entry": price, "qty": qty, "stop": stop, "target": target}

    def close(self, price: float, reason: str) -> None:
        if self.position is None:
            return
        p = self.position
        direction = 1 if p["side"] == "BUY" else -1
        pnl = (price - p["entry"]) * p["qty"] * direction
        self.balance += pnl
        self.trades.append(Trade(p["side"], p["entry"], price, p["qty"], pnl, reason))
        self.position = None

    def check_exit(self, high: float, low: float) -> None:
        if self.position is None:
            return
        p = self.position
        if p["side"] == "BUY":
            if low <= p["stop"]:
                self.close(p["stop"], "STOP_LOSS")
            elif high >= p["target"]:
                self.close(p["target"], "TAKE_PROFIT")
        else:
            if high >= p["stop"]:
                self.close(p["stop"], "STOP_LOSS")
            elif low <= p["target"]:
                self.close(p["target"], "TAKE_PROFIT")
