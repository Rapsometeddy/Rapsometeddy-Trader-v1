import pandas as pd
from bot.strategy import add_indicators, generate_signal
from bot.risk import levels, position_size

def test_indicators_are_added():
    df = pd.DataFrame({"close": range(1, 80)})
    out = add_indicators(df)
    assert "ema_fast" in out
    assert "ema_slow" in out
    assert "rsi" in out

def test_risk_levels_buy():
    stop, target = levels(100.0, "BUY")
    assert stop == 98.0
    assert target == 104.0

def test_position_size():
    assert position_size(10000.0, 100.0) == 50.0

def test_hold_before_indicators_are_ready():
    row = pd.Series({"ema_fast": float("nan"), "ema_slow": 1.0, "rsi": 50.0})
    assert generate_signal(row) == "HOLD"
