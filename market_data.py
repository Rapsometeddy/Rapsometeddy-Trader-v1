"""Fetch public AAPL market data and build a paper-only market snapshot.

This uses Yahoo Finance's public chart endpoint. It is an unofficial endpoint,
so the workflow treats the feed as best-effort and never sends orders.
"""
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from config import INITIAL_BALANCE
from bot.strategy import add_indicators, generate_signal
from backtest.engine import run
from backtest.metrics import calculate_metrics

SYMBOL = "AAPL"
RANGE = "5d"
INTERVAL = "5m"
URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/"
    + urllib.parse.quote(SYMBOL)
    + "?range=" + RANGE
    + "&interval=" + INTERVAL
    + "&includePrePost=false"
)

def fetch() -> dict:
    request = urllib.request.Request(
        URL,
        headers={"User-Agent": "Rapsometeddy-Trader/1.0"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)

def build_snapshot(payload: dict) -> dict:
    result = payload["chart"]["result"][0]
    meta = result.get("meta", {})
    quote = result["indicators"]["quote"][0]

    rows = []
    for i, timestamp in enumerate(result.get("timestamp", [])):
        values = {key: quote[key][i] for key in ("open", "high", "low", "close", "volume")}
        if any(value is None for value in values.values()):
            continue
        rows.append({
            "timestamp": int(timestamp),
            **{key: float(value) for key, value in values.items()},
        })

    frame = pd.DataFrame(rows)
    if frame.empty:
        raise RuntimeError("No market candles returned for AAPL.")

    enriched = add_indicators(frame)
    trader = run(frame, INITIAL_BALANCE)
    metrics = calculate_metrics(trader)

    candles = []
    for _, row in enriched.tail(300).iterrows():
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

    latest = enriched.iloc[-1]
    signal = generate_signal(latest)

    return {
        "symbol": SYMBOL,
        "currency": meta.get("currency", "USD"),
        "exchange": meta.get("fullExchangeName", meta.get("exchangeName", "")),
        "regular_market_price": meta.get("regularMarketPrice"),
        "latest_close": float(latest["close"]),
        "latest_timestamp": int(latest["timestamp"]),
        "signal": signal,
        "range": RANGE,
        "interval": INTERVAL,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "Yahoo Finance chart endpoint (public, unofficial)",
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
    snapshot = build_snapshot(fetch())
    path = Path("dashboard/market.json")
    path.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(
        f"AAPL {snapshot['latest_close']:.2f} "
        f"signal={snapshot['signal']} candles={len(snapshot['candles'])}"
    )

if __name__ == "__main__":
    main()
