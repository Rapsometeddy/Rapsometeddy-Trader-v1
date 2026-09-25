"""Read-only multi-FX educational market snapshot for the New York session.

This module is paper-only: it fetches public Yahoo Finance candles, filters
candles to the New York trading session, applies the existing EMA/RSI strategy,
and writes analysis data for the dashboard. It never places orders.
"""
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from config import INITIAL_BALANCE
from bot.strategy import add_indicators, generate_signal
from backtest.engine import run
from backtest.metrics import calculate_metrics

PAIRS = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "JPY=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "CAD=X",
    "USD/CHF": "CHF=X",
    "NZD/USD": "NZDUSD=X",
}
RANGE = "5d"
INTERVAL = "5m"
NY_TZ = ZoneInfo("America/New_York")


def fetch(symbol: str) -> dict:
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + urllib.parse.quote(symbol)
        + f"?range={RANGE}&interval={INTERVAL}&includePrePost=false"
    )
    request = urllib.request.Request(
        url, headers={"User-Agent": "Rapsometeddy-Trader/1.0"}
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def candles_from_payload(payload: dict) -> tuple[pd.DataFrame, dict]:
    result = payload["chart"]["result"][0]
    meta = result.get("meta", {})
    quote = result["indicators"]["quote"][0]
    rows = []

    for i, timestamp in enumerate(result.get("timestamp", [])):
        values = {k: quote[k][i] for k in ("open", "high", "low", "close", "volume")}
        if any(v is None for v in values.values()):
            continue
        rows.append({"timestamp": int(timestamp), **{k: float(v) for k, v in values.items()}})

    frame = pd.DataFrame(rows)
    if frame.empty:
        raise RuntimeError("No candles returned")

    dt = pd.to_datetime(frame["timestamp"], unit="s", utc=True).dt.tz_convert(NY_TZ)
    # New York daytime session: 08:00–17:00 local time, automatically DST-aware.
    frame = frame[(dt.dt.hour >= 8) & (dt.dt.hour < 17)].copy()
    frame["timestamp"] = frame["timestamp"].astype(int)
    return frame, meta


def analyse(pair: str, symbol: str) -> dict:
    payload = fetch(symbol)
    frame, meta = candles_from_payload(payload)
    enriched = add_indicators(frame)
    trader = run(frame, INITIAL_BALANCE)
    metrics = calculate_metrics(trader)
    latest = enriched.iloc[-1]

    candles = []
    for _, row in enriched.tail(180).iterrows():
        candles.append({
            "timestamp": int(row["timestamp"]),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": float(row["volume"]),
            "ema_fast": None if pd.isna(row["ema_fast"]) else float(row["ema_fast"]),
            "ema_slow": None if pd.isna(row["ema_slow"]) else float(row["ema_slow"]),
            "rsi": None if pd.isna(row["rsi"]) else float(row["rsi"]),
            "signal": generate_signal(row),
        })

    return {
        "pair": pair,
        "symbol": symbol,
        "currency": meta.get("currency", "USD"),
        "latest_close": float(latest["close"]),
        "latest_timestamp": int(latest["timestamp"]),
        "signal": generate_signal(latest),
        "range": RANGE,
        "interval": INTERVAL,
        "session": "New York 08:00–17:00 local time",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "paper_simulation": {
            "starting_balance": metrics.starting_balance,
            "ending_balance": metrics.ending_balance,
            "total_pnl": metrics.total_pnl,
            "return_pct": metrics.return_pct,
            "trades": metrics.trades,
            "winning_trades": metrics.winning_trades,
            "losing_trades": metrics.losing_trades,
            "win_rate_pct": metrics.win_rate_pct,
            "max_drawdown_pct": metrics.max_drawdown_pct,
        },
        "candles": candles,
    }


def main() -> None:
    markets = {}
    errors = {}
    for pair, symbol in PAIRS.items():
        try:
            markets[pair] = analyse(pair, symbol)
        except Exception as exc:
            errors[pair] = str(exc)

    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": "Yahoo Finance chart endpoint (public, unofficial)",
        "paper_only": True,
        "session_timezone": "America/New_York",
        "markets": markets,
        "errors": errors,
    }
    Path("dashboard/forex.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Updated {len(markets)} FX markets; {len(errors)} errors.")


if __name__ == "__main__":
    main()
