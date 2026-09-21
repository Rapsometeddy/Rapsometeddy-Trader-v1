# Rapsometeddy Trader v1

An educational **paper-trading and backtesting simulator**.

## What it does

Market OHLC data → EMA/RSI indicators → BUY/SELL/HOLD signal → risk model → simulated trade → results.

### v1 components

- EMA 20 / EMA 50
- RSI 14
- BUY / SELL / HOLD signals
- 1% simulated account risk per trade
- 2% simulated stop loss
- 4% simulated take profit
- Paper-trading engine
- Historical backtest engine
- Unit tests
- GitHub Actions test workflow

## Quick start

```bash
python -m pip install -r requirements.txt
pytest
```

Run the example backtest:

```bash
python run_backtest.py
```

## CSV format

For your own educational datasets, use:

```text
timestamp,open,high,low,close
2026-01-01,100,102,99,101
2026-01-02,101,103,100,102
```

## Safety

This project is intentionally **paper-only**. It does not connect to a broker, exchange, bank, or financial account and does not place real trades.

Backtests are hypothetical. They can contain assumptions, data-quality problems, and look-ahead or execution limitations, so results are not guarantees of future performance.


## AAPL market connection

The dashboard now includes a **read-only AAPL market-data feed**. A scheduled GitHub Actions job fetches recent 5-minute AAPL OHLCV candles, calculates the existing EMA 20 / EMA 50 and RSI 14 strategy, and writes a market snapshot to `dashboard/market.json`.

The feed is used only for **paper simulation**. No broker, exchange, bank, API trading key, or real-money order connection is included.

The market endpoint is an unofficial public Yahoo Finance chart endpoint and may change or rate-limit requests. The dashboard therefore labels the feed as best-effort rather than guaranteed real-time data.
